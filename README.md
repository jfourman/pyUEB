# Unreal Project Backup (Incremental)
**ALPHA**

This repository includes a Python script to create **fast, incremental backups** of an Unreal Engine project folder while avoiding huge, regeneratable directories.

The main goal is:

- Fast backups
- **Minimal steps to full recovery**
- Includes `.git` so the backup is still a usable repo snapshot
- Excludes Unreal-generated folders that can be regenerated

---

# Disclaimer
Always back up — that’s why you’re here.

Have a **separate, full backup strategy in place first**.  
I hope this script works for you as-is and in every case. However, if it doesn’t, or if your machine somehow explodes into flames, **please do not blame me**.

Take every precaution:
- Read the script
- Understand what it excludes
- **Always run with `--dry-run` first**

Improvements and contributions are always welcome.

---

## What is included?

Everything in your project folder **except** excluded patterns.

By default this keeps the important source-of-truth data needed for recovery:

- `Content/`
- `Config/`
- `Source/`
- `Plugins/`
- `*.uproject`
- `.git/` (included by default)
- Solution / project files (small, useful, optional)

---

## What is excluded by default (for speed)?

These are typically huge and safely regeneratable:

- `DerivedDataCache/`
- `Intermediate/`
- `Binaries/`
- `Saved/` *(excluded by default; can be included with a flag)*
- `Build/` *(excluded by default; can be included with a flag)*
- IDE folders like `.vs/`, `.vscode/`, `.idea/`
- Visual Studio database files `*.VC.db`, `*.VC.opendb`

---

## Backup modes

This script supports **two backup modes**:

### Incremental (default)
- Copies **only files that have changed**
- Extremely fast after the first run
- Ideal for frequent / automated backups

Mode: INCREMENTAL

### Full (--full)
- Forces a refresh copy of all eligible files
- Ignores incremental change checks
- Still respects all exclude rules
- Useful for:
	- First-time seeding of a backup location
	- Periodic “clean refresh” backups
	- Verifying full eligible project size

Mode: FULL
Even in FULL mode, excluded folders (DerivedDataCache, Intermediate, etc.) remain excluded unless explicitly included.

## Usage

### Dry run (strongly recommended)

Shows what would be copied, without copying anything:
```powershell
python pyUEB.py "D:\repo\UE5.7.1[projectName]" "E:\Backups" --dry-run --verbose
```

Example output:
Scanned: 11445
Copied: 11445
Excluded: 6
Size: 7.95 GB
[DRY RUN] No files were copied.

### Incremental backup (normal use)
```powershell
python pyUEB.py "D:\repo\UE5.7.1[projectName]" "E:\Backups"
```
Fast after the first run — only changed files are copied.

### Full backup (force refresh)
```powershell
python pyUEB.py "D:\repo\UE5.7.1[projectName]" "E:\Backups" --full
```
### Include Saved/ or Build/ (rare)
```powershell
python pyUEB.py "D:\repo\UE5.7.1[projectName]" "E:\Backups" --include-saved
python pyUEB.py "D:\repo\UE5.7.1[projectName]" "E:\Backups" --include-build
```
These are excluded by default for speed and disk usage.

### Size summary and delta reporting

By default, the script reports only the size of files copied (or would be copied).

To compute detailed size and delta information, enable:

--size-summary

Example:
```powershell
python pyUEB.py "D:\repo\UE5.7.1[projectName]" "E:\Backups" --dry-run --full --size-summary
```
Example output:
Size: 7.95 GB
Eligible: 7.95 GB
Avoided: 97.34 GB
Total: 105.29 GB
Delta: 0.00 B

### What these numbers mean

Size
Bytes copied (or that would be copied)

Eligible
Total size of all non-excluded project data
(your actual recoverable project footprint)

Avoided
Bytes skipped due to excluded folders
(DerivedDataCache, Intermediate, Saved, etc.)

Total
Eligible + Avoided
(roughly what a naïve copy-paste backup would cost)

Delta
Eligible data not copied this run
(i.e. what incremental mode saved you)

The --size-summary option walks excluded folders to compute sizes and is therefore slower.
It is off by default to keep normal backups fast.

## Git notes (Windows)

This script copies the .git directory directly to support minimal-step recovery.

On Windows, some files under .git/objects/** may be temporarily locked by:
	- Git itself
	- Antivirus or indexing services
	- Other?

When this happens:
	- The file is skipped
	- The backup continues
	- A warning is reported in the summary

This behavior is intentional — backups should not fail due to transient file locks.

Verifying a backup repo 

cd <backup-folder>
git fsck --full

If no critical errors are reported, the backup is safe to restore.

## Restore (typical workflow)

	1. Copy the backed-up project folder to the desired location
	2. Open the .uproject in Unreal Editor
	3. Regenerate project files if needed
	4. Build and run

Unreal will automatically regenerate excluded folders:
	- DerivedDataCache/
	- Intermediate/
	- Binaries/
	- Saved/ (if excluded)

## Per-project ignore rules (.backupignore)

You can add a .backupignore file to your project root to exclude additional paths without modifying the script.

Example:
### Large local media not needed for recovery
	- Content/Movies/
	- Docs/Temp/
	- *.tmp

## Status

### ALPHA
This script is actively evolving.
Review changes, verify backups, and do not rely on it as your only backup strategy.