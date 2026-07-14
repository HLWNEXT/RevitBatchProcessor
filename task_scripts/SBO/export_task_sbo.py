# -*- coding: utf-8 -*-
"""
Export job: SBO-P1-CS - weekly CAD and PDF exports.

The weekly output folder is located automatically using a glob pattern so no
manual path update is needed each week.

How to find the exact preset names in Revit:
  DWG Export Setup   -> File > Export > CAD Formats > DWG > "Export setup" dropdown
  DWG View/Sheet Set -> same dialog > "Export list" dropdown
  PDF Export Setup   -> File > Export > PDF > "PDF Setup" dropdown  (Revit 2022+)
  PDF View/Sheet Set -> same PDF dialog > "Selected views/sheets" named set
"""

import os
import sys
import glob
import revit_script_util
from revit_script_util import Output
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(revit_script_util.GetTaskScriptFilePath()))))
import revit_export_util

doc             = revit_script_util.GetScriptDocument()
uiapp           = revit_script_util.GetUIApplication()
revit_file_path = revit_script_util.GetRevitFilePath()

# Locate the current weekly folder automatically.
# Pattern matches any folder ending in "- SBO-P1-CS - WEEKLY UPLOAD" on the Desktop.
# sorted() picks the most recent when multiple exist (YYYY_MMDD sorts chronologically).
DESKTOP = r"C:\Users\smadera\OneDrive - HLW International LLP\Desktop"
WEEKLY_PATTERN = "* - SBO-P1-CS - WEEKLY UPLOAD"

matches = sorted(glob.glob(os.path.join(DESKTOP, WEEKLY_PATTERN)))
if not matches:
    raise Exception("No weekly folder found matching: " + os.path.join(DESKTOP, WEEKLY_PATTERN))
weekly_folder = matches[-1]
Output("Weekly folder: " + weekly_folder)

# -- CONFIGURE FOR THIS JOB --------------------------------------------------
EXPORTS = [
    {
        "type":                "DWG",
        "setup":               "Architectural - Internal Coordinates",
        "sheet_set":           ".CAD EXPORT - 02A_CAD",
        "output":              os.path.join(weekly_folder, "02_CAD", "02A_CAD"),
        "date_subfolder":      False,
        "rename_strip_prefix": "US-SBO-F0K1_",
        "delete_pcp":          True,
    },
    {
        "type":                "DWG",
        "setup":               "Architectural - Internal Coordinates",
        "sheet_set":           ".CAD EXPORT - 02B_CAD RCP FOR FP",
        "output":              os.path.join(weekly_folder, "02_CAD", "02B_CAD RCP FOR FP"),
        "date_subfolder":      False,
        "rename_strip_prefix": "US-SBO-F0K1_",
        "delete_pcp":          True,
    },
    {
        "type":           "PDF",
        "setup":          "SBO-P1-CS - Overall Plans",
        "sheet_set":      ".PDF WEEKLY EXPORT - VIEWS (Overall plans)",
        "output":         os.path.join(weekly_folder, "03_PDF"),
        "date_subfolder": False,
        "pdf_filename":   "SBO-P1-CS - Overall Plans",
    },
    {
        "type":           "PDF",
        "setup":          "SBO-P1-CS - Progress Set",
        "sheet_set":      ".PDF WEEKLY EXPORT - SHEETS (Progress set)",
        "output":         os.path.join(weekly_folder, "03_PDF"),
        "date_subfolder": False,
        "pdf_filename":   "SBO-P1-CS - Progress Set",
    },
]
# ----------------------------------------------------------------------------

Output("Job start: " + revit_file_path)

Output("Clearing output folders...")
seen_folders = set()
for cfg in EXPORTS:
    folder = cfg["output"]
    if folder not in seen_folders:
        seen_folders.add(folder)
        revit_export_util.clear_folder_contents(folder)

revit_export_util.run_exports(doc, uiapp, EXPORTS)
Output("Cleaning up Revit backups...")
revit_export_util.cleanup_revit_backups(revit_file_path)
Output("Renaming weekly folder...")
revit_export_util.rename_weekly_folder(weekly_folder)
Output("Job complete.")
