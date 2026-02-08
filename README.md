# Unreal Project Backup (Incremental)

This repository includes a Python script to create **fast, incremental backups** of an Unreal Engine project folder while avoiding huge, regeneratable directories.

The main goal is:

- **FAST backups**
- **Minimal steps to full recovery**
- Includes `.git` so the backup is still a usable repo snapshot
- Excludes Unreal-generated folders that can be regenerated

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

## Usage

### Dry run (recommended first)

Shows what would be copied without actually copying:

```powershell
python pyUEB.py "D:\repo\UE5.7.1\EchoesOfNevermore" "E:\Backups" --dry-run --verbose

