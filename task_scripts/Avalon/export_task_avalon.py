# -*- coding: utf-8 -*-
"""
Export job: Project Avalon - weekly CAD and PDF backgrounds for 6 buildings.

Runs once per file. The output subfolder is derived automatically from the
document title (e.g. "Project Avalon_Building 20_AI_26" -> "Building 20").

How to find the exact preset names in Revit:
  DWG Export Setup   -> File > Export > CAD Formats > DWG > "Export setup" dropdown
  DWG View/Sheet Set -> same dialog > "Export list" dropdown
  Print Setup        -> File > Print > Print Setup dropdown
"""

import os
import re
import sys
import glob
import revit_script_util
from revit_script_util import Output
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(revit_script_util.GetTaskScriptFilePath()))))
import revit_export_util

doc             = revit_script_util.GetScriptDocument()
uiapp           = revit_script_util.GetUIApplication()
revit_file_path = revit_script_util.GetRevitFilePath()

# Derive "Building 20", "Building 21", etc. from the document title.
m = re.search(r'Building \d+', doc.Title)
building_name = m.group(0) if m else doc.Title
Output("Building: " + building_name)

# Locate the current weekly folder automatically.
DESKTOP = r"C:\Users\smadera\OneDrive - HLW International LLP\Desktop"
WEEKLY_PATTERN = "* - AVALON - CAD AND PDF BACKGROUNDS"

matches = sorted(glob.glob(os.path.join(DESKTOP, WEEKLY_PATTERN)))
if not matches:
    raise Exception("No weekly folder found matching: " + os.path.join(DESKTOP, WEEKLY_PATTERN))
weekly_folder = matches[-1]
Output("Weekly folder: " + weekly_folder)

# -- CONFIGURE FOR THIS JOB --------------------------------------------------
EXPORTS = [
    {
        "type":         "DWG",
        "setup":        "WEEKLY EXPORTS",
        "sheet_set":    "WEEKLY EXPORTS",
        "output":       weekly_folder,
        "delete_pcp":   True,
        # "Project Avalon_Building 20_AI_26-Sheet - A-060-1 - OVERALL SLAB PLANS - BUILDING 20"
        # ->  "A-060 - OVERALL SLAB PLANS - BUILDING 20"
        "rename_regex": (r'^.*Sheet - (A-[A-Z0-9]+)-\d+( - .+)$', r'\1\2'),
    },
    {
        "type":           "PDF",
        "setup":          "Anduril",
        "sheet_set":      "WEEKLY EXPORTS",
        "output":         weekly_folder,
        "pdf_individual": True,
        # Naming rule in Revit: Sheet Number - Sheet Name
        # Raw output: "A-060.1 - OVERALL SLAB PLANS - BUILDING 27.pdf"
        # After regex: "A-060 - OVERALL SLAB PLANS - BUILDING 27.pdf"
        "rename_regex":   (r'^(A-[A-Z0-9]+)\.\d+( - .+)$', r'\1\2'),
    },
]
# ----------------------------------------------------------------------------

Output("Job start: " + revit_file_path)

# Clear the output folder only if it contains files from a previous run.
# All 6 buildings write to the same folder sequentially, so we must not clear
# mid-batch — only the first building (which sees last week's files) should clear.
import datetime
_should_clear = False
if os.path.exists(weekly_folder):
    _today = datetime.date.today()
    for _f in os.listdir(weekly_folder):
        _fp = os.path.join(weekly_folder, _f)
        if os.path.isfile(_fp):
            _mtime = datetime.date.fromtimestamp(os.path.getmtime(_fp))
            if _mtime < _today:
                _should_clear = True
                break
if _should_clear:
    Output("Clearing output folder (previous week's files detected)...")
    revit_export_util.clear_folder_contents(weekly_folder)

revit_export_util.run_exports(doc, uiapp, EXPORTS)
Output("Renaming weekly folder...")
revit_export_util.rename_weekly_folder(weekly_folder)
Output("Job complete.")
