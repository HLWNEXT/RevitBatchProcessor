# -*- coding: utf-8 -*-
"""
Post-processing for Project Avalon weekly exports.

Combines all individual PDFs into a single weekly PDF (with page labels),
then zips the entire weekly folder.

Requires Python 3 and pypdf:
    pip install pypdf

Usage:
    python avalon_post_combine.py "<weekly_folder_path>"
"""

import os
import re
import shutil
import sys
import zipfile

SERVER_FOLDER = r"\\hlw.com\projects\LA\2026\26047\2-MODEL\3-CAD\PLOT\ARCH"

try:
    from pypdf import PdfWriter, PdfReader
    from pypdf.generic import (
        ArrayObject,
        DictionaryObject,
        NameObject,
        NumberObject,
        TextStringObject,
    )
except ImportError:
    print("ERROR: pypdf is not installed. Run:  pip install pypdf")
    sys.exit(1)


def _building_sort_key(filename):
    """Sort key: (building_number, sheet_number_string) for correct page order."""
    bld = re.search(r'BUILDING\s+(\d+)', filename, re.IGNORECASE)
    sheet = re.match(r'A-([A-Z0-9]+)', filename)
    return (
        int(bld.group(1)) if bld else 999,
        sheet.group(1) if sheet else filename,
    )


def combine_pdfs(weekly_folder, output_path):
    """
    Merge individual PDFs into one file and set PDF page labels (BLD 20, BLD 21, …).
    Files are sorted by building number then sheet number.
    Skips any file whose name ends with 'WEEKLY EXPORT.pdf' to avoid re-merging.
    """
    pdf_files = sorted(
        [f for f in os.listdir(weekly_folder)
         if f.lower().endswith('.pdf') and not f.upper().endswith('WEEKLY EXPORT.PDF')],
        key=_building_sort_key,
    )

    if not pdf_files:
        print("WARNING: no individual PDFs found in " + weekly_folder)
        return

    print("Combining {} PDFs...".format(len(pdf_files)))

    writer = PdfWriter()
    page_label_ranges = []  # [(start_page_index, "BLD XX"), ...]
    current_page = 0
    current_building = None

    for filename in pdf_files:
        filepath = os.path.join(weekly_folder, filename)
        reader = PdfReader(filepath)

        bld = re.search(r'BUILDING\s+(\d+)', filename, re.IGNORECASE)
        label = "BLD {}".format(bld.group(1)) if bld else "BLD ??"

        if label != current_building:
            page_label_ranges.append((current_page, label))
            current_building = label

        for page in reader.pages:
            writer.add_page(page)

        print("  + {} ({} page(s))".format(filename, len(reader.pages)))
        current_page += len(reader.pages)

    # Set PDF page labels so viewers show "BLD 20", "BLD 21", etc.
    # /PageLabels /Nums is a flat array of pairs: [page_index, label_dict, ...]
    nums = ArrayObject()
    for start_idx, label in page_label_ranges:
        nums.append(NumberObject(start_idx))
        nums.append(DictionaryObject({NameObject("/P"): TextStringObject(label)}))

    writer._root_object[NameObject("/PageLabels")] = DictionaryObject({
        NameObject("/Nums"): nums
    })

    with open(output_path, "wb") as f:
        writer.write(f)

    print("Combined PDF -> {}".format(os.path.basename(output_path)))
    print("Total pages: {}".format(current_page))


def zip_folder(weekly_folder, zip_path):
    """Zip all files in weekly_folder into zip_path (the zip itself is excluded)."""
    zip_name = os.path.basename(zip_path)
    files = [
        f for f in os.listdir(weekly_folder)
        if os.path.isfile(os.path.join(weekly_folder, f)) and f != zip_name
    ]

    print("Zipping {} file(s)...".format(len(files)))
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filename in files:
            zf.write(os.path.join(weekly_folder, filename), filename)
            print("  + " + filename)

    print("Zip -> {}".format(zip_name))


def copy_to_server(weekly_folder, combined_pdf_path, folder_name):
    """
    Copy the combined PDF (loose) and the entire weekly folder to the server.
    Logs a warning and continues if the server is not reachable.
    """
    if not os.path.isdir(SERVER_FOLDER):
        print("WARNING: server not reachable, skipping copy: " + SERVER_FOLDER)
        return

    print("Copying to server: " + SERVER_FOLDER)

    # Combined PDF — copied loose into the server folder
    try:
        shutil.copy2(combined_pdf_path, SERVER_FOLDER)
        print("  Copied: " + os.path.basename(combined_pdf_path))
    except Exception as e:
        print("  WARNING: could not copy combined PDF: " + str(e))

    # Entire weekly folder — copied as a subfolder on the server
    dest = os.path.join(SERVER_FOLDER, folder_name)
    try:
        shutil.copytree(weekly_folder, dest, dirs_exist_ok=True)
        print("  Copied folder: " + folder_name)
    except Exception as e:
        print("  WARNING: could not copy folder: " + str(e))


def main(weekly_folder):
    if not os.path.isdir(weekly_folder):
        print("ERROR: folder not found: " + weekly_folder)
        sys.exit(1)

    folder_name = os.path.basename(weekly_folder)

    # Extract date prefix from folder name (e.g. "2026_0724 - AVALON - ...")
    date_match = re.match(r'^(\d{4}_\d{4})', folder_name)
    if date_match:
        date_prefix = date_match.group(1)
    else:
        from datetime import date
        date_prefix = date.today().strftime("%Y_%m%d")

    combined_pdf_name = "{} - WEEKLY EXPORT.pdf".format(date_prefix)
    combined_pdf_path = os.path.join(weekly_folder, combined_pdf_name)

    # Zip takes the same name as the folder
    zip_path = os.path.join(weekly_folder, folder_name + ".zip")

    combine_pdfs(weekly_folder, combined_pdf_path)
    zip_folder(weekly_folder, zip_path)
    copy_to_server(weekly_folder, combined_pdf_path, folder_name)

    print("Done.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python avalon_post_combine.py \"<weekly_folder_path>\"")
        sys.exit(1)
    main(sys.argv[1])
