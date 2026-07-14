# -*- coding: utf-8 -*-
"""
Export job template - copy this file for each new project/job.
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
        "setup":          "DWG Setup A",         # exact name from Revit UI
        "sheet_set":      "Issue Set 1",          # exact name from Revit UI
        "output":         r"C:\Exports\ProjectA\DWG\Set1",
        "date_subfolder": True,                   # creates ...\Set1\2024-11-15\ each run
        "strip_before_A": True,                   # "20241115 - A100 Plan.dwg" -> "A100 Plan.dwg"
        "delete_pcp":     True,                   # remove .pcp files Revit generates
    },
    {
        "type":           "PDF",
        "setup":          "PDF Setup A",
        "sheet_set":      "Issue Set 1",
        "output":         r"C:\Exports\ProjectA\PDF\Set1",
        "date_subfolder": True,
        "pdf_filename":   "ProjectA_IssueSet1",  # combined PDF filename, no extension
    },
]
# ----------------------------------------------------------------------------

import os
import sys
import revit_script_util
from revit_script_util import Output
# If this script is in a subfolder, add the parent (task_scripts/) to the path
# so revit_export_util.py can be found. Remove this line if the script is in the root folder.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(revit_script_util.GetTaskScriptFilePath()))))
import revit_export_util

doc   = revit_script_util.GetScriptDocument()
uiapp = revit_script_util.GetUIApplication()

Output("Job start: " + revit_script_util.GetRevitFilePath())
revit_export_util.run_exports(doc, uiapp, EXPORTS)
Output("Job complete.")
