# -*- coding: utf-8 -*-
"""
RBP task script for upgrading family TEMPLATE (.rft) files.

Family templates can't be opened with Application.OpenDocumentFile - not even
after renaming to .rfa, since Revit reads an internal marker in the file (not
the extension) and rejects templates there. The correct API is
Application.NewFamilyDocument(), which is what File > New > Family calls in
the UI, followed by SaveAs() back onto the same .rft path.

RBP itself is only used to launch a Revit session and invoke this script once
(against a throwaway anchor project - see run_family_upgrade.ps1). All the
real work happens in the loop below, independent of whatever file RBP opened.
"""
import os
import sys
import revit_script_util
from revit_script_util import Output
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(revit_script_util.GetTaskScriptFilePath()))))

import family_template_util
from family_template_util import cleanup_rft_backups, describe_exception, RFT_BACKUP_PATTERN

from Autodesk.Revit.DB import SaveAsOptions

FOLDER = r"C:\Users\smadera\OneDrive - HLW International LLP\Desktop\FAMILY TEMP"

uiapp = revit_script_util.GetUIApplication()
app = uiapp.Application

rft_files = sorted(
    os.path.join(FOLDER, f) for f in os.listdir(FOLDER)
    if f.lower().endswith(".rft") and not RFT_BACKUP_PATTERN.search(f)
)
Output("Found {} .rft file(s) in {}".format(len(rft_files), FOLDER))

save_as_options = SaveAsOptions()
save_as_options.OverwriteExistingFile = True

succeeded = 0
failed = 0
for path in rft_files:
    Output("Processing: " + path)
    try:
        size_bytes = os.path.getsize(path)
        is_readonly = not os.access(path, os.W_OK)
        Output("  size={} bytes, read_only={}".format(size_bytes, is_readonly))
    except OSError as e:
        Output("  WARNING: could not stat file: " + str(e))

    doc = None
    try:
        doc = app.NewFamilyDocument(path)
        doc.SaveAs(path, save_as_options)
        doc.Close(False)
        doc = None
        succeeded += 1
        Output("  OK")
    except Exception as e:
        failed += 1
        Output("  ERROR: " + describe_exception(e))
        if doc is not None:
            try:
                doc.Close(False)
            except Exception:
                pass

Output("Cleaning up .rft backup files...")
cleanup_rft_backups(FOLDER)

Output("Job complete. {} succeeded, {} failed.".format(succeeded, failed))
