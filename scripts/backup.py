"""Copy the project to a backup folder, then verify the copy.

Usage: python scripts/backup.py DEST_DIR [--skip-git]

Additive and safe: files are copied only when missing at the destination or when the source is newer
or a different size. Nothing at the destination is ever deleted or overwritten with an older file.
Skipped: .venv, __pycache__ (rebuildable), and with --skip-git also the .git folder.
"""
import shutil
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".venv", "__pycache__"}


def files(root: Path, skip_git: bool):
    skip = SKIP_DIRS | ({".git"} if skip_git else set())
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts[:-1]) & skip):
            yield p


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    dest = Path(sys.argv[1])
    skip_git = "--skip-git" in sys.argv
    if dest.resolve() == SRC:
        sys.exit("Destination is the source folder.")
    copied = kept = 0
    for p in files(SRC, skip_git):
        q = dest / p.relative_to(SRC)
        s = p.stat()
        if q.exists() and q.stat().st_size == s.st_size and q.stat().st_mtime >= s.st_mtime:
            kept += 1
            continue
        if q.exists() and q.stat().st_mtime > s.st_mtime:
            kept += 1  # destination is newer: leave it alone
            continue
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)
        copied += 1
    missing = [p for p in files(SRC, skip_git) if not (dest / p.relative_to(SRC)).exists()]
    total = sum(1 for _ in files(SRC, skip_git))
    print(f"Copied {copied}, already up to date {kept}, source files {total}, missing at destination {len(missing)}")
    print(f"Backup: {dest}")
    if missing:
        sys.exit(1)


if __name__ == "__main__":
    main()
