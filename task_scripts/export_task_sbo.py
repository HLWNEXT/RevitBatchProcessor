# -*- coding: utf-8 -*-
"""
Export job: SBO-P1-CS - weekly CAD and PDF exports.
Edit only the EXPORTS list below. Do not modify revit_export_util.py.

How to find the exact preset names in Revit:
  DWG Export Setup   -> File > Export > CAD Formats > DWG > "Export setup" dropdown
  DWG View/Sheet Set -> same dialog > "Export list" dropdown
  PDF Export Setup   -> File > Export > PDF > "PDF Setup" dropdown  (Revit 2022+)
  PDF View/Sheet Set -> same PDF dialog > "Selected views/sheets" named set
"""

# -- CONFIGURE FOR THIS JOB --------------------------------------------------
EXPORTS = [
    {
        "type":           "DWG",
        "setup":          "Architectural - Internal Coordinates",
        "sheet_set":      ".CAD EXPORT - 02A_CAD",
        "output":         r"C:\Users\smadera\OneDrive - HLW International LLP\Desktop\2026_0630 - SBO-P1-CS - WEEKLY UPLOAD\TEST\CAD",
        "date_subfolder":      False,
        "rename_strip_prefix": "US-SBO-F0K1_",  # keeps "A - PLAN - EXPORT - L1" -> "A-PLAN-EXPORT-L1"
        "delete_pcp":          True,
    },
    {
        "type":           "PDF",
        "setup":          "SBO-P1-CS - Overall Plans",
        "sheet_set":      ".PDF WEEKLY EXPORT - VIEWS (Overall plans)",
        "output":         r"C:\Users\smadera\OneDrive - HLW International LLP\Desktop\2026_0630 - SBO-P1-CS - WEEKLY UPLOAD\TEST\PDF",
        "date_subfolder": False,
        "pdf_filename":   "SBO-P1-CS - Overall Plans",
    },
]
# ----------------------------------------------------------------------------

import revit_script_util
import revit_export_util
from revit_script_util import Output

doc   = revit_script_util.GetScriptDocument()
uiapp = revit_script_util.GetUIApplication()

revit_file_path = revit_script_util.GetRevitFilePath()
Output("Job start: " + revit_file_path)
revit_export_util.run_exports(doc, uiapp, EXPORTS)
Output("Cleaning up Revit backups...")
revit_export_util.cleanup_revit_backups(revit_file_path)
Output("Job complete.")
