# Unreal Project Backup (Incremental)
ALPHA
This repository includes a Python script to create **fast, incremental backups** of an Unreal Engine project folder while avoiding huge, regeneratable directories.

The main goal is:

- **FAST backups**
- **Minimal steps to full recovery**
- Includes `.git` so the backup is still a usable repo snapshot
- Excludes Unreal-generated folders that can be regenerated

---

# Disclaimer
Always backup, that's why you're here. Have a full backup in place first.
I hope this script works for you as is and in every case. 
However if it doesn't or somehow your machine explodes into flames, please do not blame me.
Take every precaution and run a --dry-run first.

Improvements are always welcome!

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

