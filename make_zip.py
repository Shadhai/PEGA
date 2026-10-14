"""
Build a Kaggle-compatible zip of the ablation package.
Skips __pycache__, .backup files, and uses forward slashes (ZIP spec).
"""

import os
import zipfile
from pathlib import Path

SRC_DIR = Path("cint70_package")
OUT_ZIP = Path("cint70_ablation.zip")

# Folders and files to skip
SKIP_DIRS = {"__pycache__", ".git", ".pytest_cache", "venv", "models"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".backup"}

if OUT_ZIP.exists():
    OUT_ZIP.unlink()

count = 0
with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for root, dirs, files in os.walk(SRC_DIR):
        # Prune unwanted directories
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for filename in files:
            if any(filename.endswith(s) for s in SKIP_SUFFIXES):
                continue

            file_path = Path(root) / filename
            # Arcname uses forward slashes automatically when given a Path
            arcname = file_path.relative_to(SRC_DIR.parent).as_posix()

            zf.write(file_path, arcname=arcname)
            count += 1
            print(f"  + {arcname}")

print(f"\n✅ Wrote {count} files to {OUT_ZIP}")
print(f"   Size: {OUT_ZIP.stat().st_size / 1e6:.2f} MB")