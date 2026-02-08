#!/usr/bin/env python3
"""
Incremental Unreal Project Backup

Goal:
- Produce FAST backups of an Unreal Engine project folder
- Include whats needed for FULL recovery:
  - Content/, Config/, Source/, Plugins/, *.uproject
  - .git (so the backup remains a usable repo snapshot)
  - solution/project files (optional, but tiny vs Content)
- Exclude files/folders that Unreal can regenerate safely:
  - DerivedDataCache/, Intermediate/, Binaries/
  - Saved/ (usually big and regeneratable; can be included via flag)
  - Build/ (often not required; can be included via flag)

Backup style:
- Incremental mirror copy:
  - Only copy files that changed (based on size + modified time)
  - Does NOT delete files from the backup target  

PowerShell examples (double backslash for example only):
  python backup_unreal.py "D:\\repo\\UE5.7.1\\[projectName]" "J:\\Backups" --dry-run --verbose
  python backup_unreal.py "D:\\repo\\UE5.7.1\\[projectName]" "J:\\Backups"  
  python backup_unreal.py "D:\\repo\\UE5.7.1\\[projectName]" "J:\\Backups" --full   (forces refresh copies, probably never really needed)
  python backup_unreal.py "D:\\repo\\UE5.7.1\\[projectName]" "J:\\Backups" --full --include-saved --include-build (refresh + include Saved and Build (rare))

"""

import argparse
import fnmatch
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


# -----------------------------------------------------------------------------
# Default excludes optimized for:
# - FAST backups and minimal recovery steps
# - We DO NOT exclude .git by default
# - Saved/ and Build/ are excluded by default but can be included via flags.
# -----------------------------------------------------------------------------
DEFAULT_EXCLUDES = [
    "Binaries/",
    "DerivedDataCache/",
    "Intermediate/",
    ".vs/",
    ".idea/",
    ".vscode/",
    "*.VC.db",
    "*.VC.opendb",
]

# -----------------------------------------------------------------------------
# Human readable size formatting
# -----------------------------------------------------------------------------
def format_bytes(num_bytes: int) -> str:
    """
    Convert bytes to a human-readable string.
    """
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if num_bytes < 1024:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024

    return f"{num_bytes:.2f} PB"

# -----------------------------------------------------------------------------
# Normalize relative paths to forward slash form so matching behaves the same
# on Windows and Linux e.g.(Content\\Foo\\Bar.uasset" -> "Content/Foo/Bar.uasset)
# -----------------------------------------------------------------------------
def norm_rel(rel: str) -> str:    
    return rel.replace("\\", "/")

# -----------------------------------------------------------------------------
# Optional per-project ignore file: .backupignore
# Put .backupignore in the project root to add patterns without modifying code.
# Format:
# - One pattern per line
# - Blank lines and lines starting with # are ignored
# - Directory patterns should end with "/"
# - Wildcards are supported (fnmatch)
# Example .backupignore:
#   # Exclude huge local media not needed for recovery
#    Content/Movies/
#    Docs/Temp/
#    *.tmp
# -----------------------------------------------------------------------------
def load_ignore_file(project_root: Path) -> list[str]:    
    ignore_path = project_root / ".backupignore"
    if not ignore_path.exists():
        return []

    patterns: list[str] = []
    for line in ignore_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line)

    return patterns

# -----------------------------------------------------------------------------
# True if rel path matches any pattern.
# Rules:
#  - Directory patterns end in "/": they match the directory and everything under it
#  - Other patterns use fnmatch: "*.sln", "Config/*.ini", etc.
# -----------------------------------------------------------------------------
def match_any(rel: str, patterns: list[str]) -> bool:
    rel = norm_rel(rel)

    for pat in patterns:
        pat_norm = norm_rel(pat.strip())
        if not pat_norm:
            continue

        if pat_norm.endswith("/"):
            # Directory match by prefix
            if rel == pat_norm[:-1] or rel.startswith(pat_norm):
                return True
        else:
            if fnmatch.fnmatch(rel, pat_norm):
                return True

    return False

# -----------------------------------------------------------------------------
# Incremental copy:
#  - copy if destination missing
#  - copy if file size differs
#  - copy if modified time differs (rounded to seconds)
# This is intentionally fast and "good enough" for backup mirroring.
# -----------------------------------------------------------------------------
def should_copy(src: Path, dst: Path) -> bool:
    if not dst.exists():
        return True

    try:
        s = src.stat()
        d = dst.stat()
    except FileNotFoundError:
        return True

    if s.st_size != d.st_size:
        return True

    return int(s.st_mtime) != int(d.st_mtime)


@dataclass
class Stats:
    scanned: int = 0        # eligible files encountered
    copied: int = 0         # files copied (changed/new)
    skipped: int = 0        # files skipped (unchanged)
    excluded: int = 0       # excluded dirs + excluded files
    bytes_copied: int = 0   # total size of copied / would-copy files
    failed: int = 0         # files that failed to copy (permissions, locks)

# -----------------------------------------------------------------------------
# Backup a project folder to: <target>/<ProjectFolderName>/
#  - Walk the source tree
#  - Prune excluded directories early (big speed win)
#  - Copy only changed files
#  - If force_copy=True, copy all eligible files (FULL backup mode)
# -----------------------------------------------------------------------------
def backup_project(source: Path, target: Path, excludes: list[str], dry_run: bool, verbose: bool, force_copy: bool) -> None:
    stats = Stats()

    source = source.resolve()
    target = target.resolve()

    if not source.exists():
        raise FileNotFoundError(f"Source path does not exist: {source}")

    # Keep backups clean: each project gets its own folder under target
    target_root = target / source.name
    if not dry_run:
        target_root.mkdir(parents=True, exist_ok=True)

    ignore_file_patterns = load_ignore_file(source)
    all_excludes = excludes + ignore_file_patterns

    if verbose:
        print("=== Backup Config ===")
        print(f"Source: {source}")
        print(f"Target: {target_root}")
        print("Excludes:")
        for p in all_excludes:
            print(f"  - {p}")
        print("=====================\n")

    for root, dirs, files in os.walk(source):
        root_p = Path(root)
        rel_root = norm_rel(str(root_p.relative_to(source)))

        # Prune excluded directories so os.walk doesn't traverse them
        pruned_dirs = []
        for d in list(dirs):
            rel_dir = norm_rel(str(Path(rel_root) / d)) + "/"
            if match_any(rel_dir, all_excludes):
                pruned_dirs.append(d)
                stats.excluded += 1
        for d in pruned_dirs:
            dirs.remove(d)

        # Ensure destination directory exists
        dst_dir = target_root / (Path(rel_root) if rel_root != "." else Path())
        if not dry_run:
            dst_dir.mkdir(parents=True, exist_ok=True)

        for f in files:
            src_file = root_p / f
            rel_file = norm_rel(str(src_file.relative_to(source)))

            # Exclude files by pattern
            if match_any(rel_file, all_excludes):
                stats.excluded += 1
                if verbose:
                    print(f"[EXCLUDE] {rel_file}")
                continue

            stats.scanned += 1
            dst_file = target_root / Path(rel_file)
            
            # Actually copy
            #  - Incremental mode: copy only if changed
            #  - Full mode: always copy eligible files
            if force_copy or should_copy(src_file, dst_file):
                file_size = src_file.stat().st_size
                stats.copied += 1
                stats.bytes_copied += file_size

                if dry_run:
                    print(f"[WOULD COPY] {rel_file}")
                else:
                    try:
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        if verbose:
                            print(f"[COPIED] {rel_file}")
                    except PermissionError as e:
                        stats.failed += 1
                        if verbose:
                            print(f"[FAILED] {rel_file} (permission denied)")
                    except OSError as e:
                        stats.failed += 1
                        if verbose:
                            print(f"[FAILED] {rel_file} ({e})")
            else:
                stats.skipped += 1
                if verbose:
                    print(f"[SKIP] {rel_file}")

    print("\n=== Backup Summary ===")
    print(f"Mode:     {'FULL' if force_copy else 'INCREMENTAL'}")
    print(f"Source:   {source}")
    print(f"Target:   {target_root}")
    print(f"Scanned:  {stats.scanned}")
    print(f"Copied:   {stats.copied}")
    print(f"Skipped:  {stats.skipped}")
    print(f"Excluded: {stats.excluded}")
    print(f"Failed:   {stats.failed}")
    print(f"Size:     {format_bytes(stats.bytes_copied)}")
    if dry_run:
        print("[DRY RUN] No files were copied.")

# -----------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Fast incremental backup for Unreal Engine project folders.")
    ap.add_argument("source", help="Path to UE project folder (contains .uproject).")
    ap.add_argument("target", help="Directory where backups should be stored.")
    ap.add_argument("--full", action="store_true", help="FULL backup mode: copy all eligible files (ignores incremental checks).")
    ap.add_argument("--dry-run", action="store_true", help="Print actions without copying files.")
    ap.add_argument("--verbose", action="store_true", help="Print excludes and per-file decisions.")

    # Saved/ and Build/ are excluded by default for speed. Can include them if needed.
    ap.add_argument("--include-saved", action="store_true", help="Include Saved/ (logs, autosaves, local saves). Usually large.")
    ap.add_argument("--include-build", action="store_true", help="Include Build/ (often not required for recovery).")

    # For future: if ever ran against a parent folder that includes Engine/
    ap.add_argument("--exclude-engine", action="store_true", help="Exclude Engine/ if it exists UNDER the source folder.")

    args = ap.parse_args()

    excludes = list(DEFAULT_EXCLUDES)
    
    if not args.include_saved:
        excludes.append("Saved/")
    if not args.include_build:
        excludes.append("Build/")
    if args.exclude_engine:
        excludes.append("Engine/")

    backup_project(
        source=Path(args.source),
        target=Path(args.target),
        excludes=excludes,
        dry_run=args.dry_run,
        verbose=args.verbose,
        force_copy=args.full
    )

# -----------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    main()
