#!/usr/bin/env python3
"""
Extract all JPEG/JPG files from multiple Google Photos zip archives
into a single destination directory while preserving each image's
Google Photos subfolder name.

Features:
    • Merges subfolders of the same name from different zips.
    • Appends a numeric suffix if files collide.
    • Skips invalid/corrupted zip files and reports them.
    • Prints an alphabetically sorted list of all zips successfully processed.

Usage:
    python script.py /path/to/source_zips /path/to/destination
"""

import sys
import zipfile
from zipfile import BadZipFile
from pathlib import Path
import shutil

def main():
    # ---- 1. Parse command-line arguments ----
    if len(sys.argv) != 3:
        print("Usage: python script.py <source_dir> <destination_dir>")
        sys.exit(1)

    source_dir = Path(sys.argv[1]).expanduser().resolve()
    dest_dir   = Path(sys.argv[2]).expanduser().resolve()

    # Ensure destination directory exists
    dest_dir.mkdir(parents=True, exist_ok=True)

    successful_zips = []   # Keep track of zips that were processed without error
    skipped_zips    = []   # Keep track of invalid/corrupt zips

    # ---- 2. Iterate through every .zip in the source directory ----
    for zip_path in sorted(source_dir.glob("*.zip"), key=lambda p: p.name.lower()):
        print(f"Processing {zip_path.name} …")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                # Go through each file in the archive
                for member in zf.infolist():
                    # Skip directories
                    if member.is_dir():
                        continue

                    member_path = Path(member.filename)

                    # Require 'Google Photos' in the path
                    if "Google Photos" not in member_path.parts:
                        continue

                    # Only accept .jpg/.jpeg (case-insensitive)
                    if member_path.suffix.lower() not in {".jpg", ".jpeg"}:
                        continue

                    # Subfolders inside 'Google Photos'
                    gp_index   = member_path.parts.index("Google Photos")
                    subfolders = member_path.parts[gp_index + 1:-1]  # all folders after Google Photos

                    # Destination folder
                    target_folder = dest_dir.joinpath(*subfolders)
                    target_folder.mkdir(parents=True, exist_ok=True)

                    # Handle duplicate filenames
                    filename   = member_path.name
                    final_path = target_folder / filename
                    counter    = 1
                    while final_path.exists():
                        stem, ext = final_path.stem, final_path.suffix
                        final_path = target_folder / f"{stem}_{counter}{ext}"
                        counter += 1

                    # Extract file directly to final destination
                    with zf.open(member) as source_file, open(final_path, "wb") as out_file:
                        shutil.copyfileobj(source_file, out_file)

            # If we reach here without exception, record success
            successful_zips.append(zip_path.name)

        except BadZipFile:
            print(f"⚠️  Skipping {zip_path.name}: not a valid zip file.")
            skipped_zips.append(zip_path.name)
        except Exception as e:
            print(f"⚠️  Skipping {zip_path.name}: unexpected error ({e})")
            skipped_zips.append(zip_path.name)

    # ---- 3. Summary ----
    print("\n=== Summary ===")
    if successful_zips:
        print("Successfully processed zip files (sorted by name):")
        for name in sorted(successful_zips, key=str.lower):
            print("  •", name)
    else:
        print("No zip files were successfully processed.")

    if skipped_zips:
        print("\nSkipped zip files:")
        for name in skipped_zips:
            print("  •", name)

    print("\n✅ Finished extracting JPEGs.")

if __name__ == "__main__":
    main()