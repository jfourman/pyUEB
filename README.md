# Unreal Project Backup (Incremental)
**ALPHA**

This repository includes a Python script to create **fast, incremental backups** of an Unreal Engine project folder while avoiding huge, regeneratable directories.

The main goal is:

- **FAST backups**
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

```text
Mode: INCREMENTAL
