# -*- coding: utf-8 -*-
"""
RBP task script: create metric copies of imperial family templates.

For every .rft in FOLDER (skipping any that already end in _metric.rft),
opens it via NewFamilyDocument - family templates require this API rather
than OpenDocumentFile, same reason as upgrade_families_task.py - switches
its unit settings to metric, and saves the result under a new name with a
"_metric" suffix (e.g. Planting_HLW.rft -> Planting_HLW_metric.rft). The
original file is left untouched.

Revit's unit settings are independent per spec (Length, Area, Volume, ...)
even though some are mathematically derived from others, so each one needed
has to be set explicitly - there is no single imperial/metric switch.

RBP itself is only used to launch a Revit session and invoke this script
once (against a throwaway anchor project - see run_metric_conversion.ps1).
All the real work happens in the loop below, independent of whatever file
RBP opened.
"""
import os
import sys
import revit_script_util
from revit_script_util import Output
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(revit_script_util.GetTaskScriptFilePath()))))

from family_template_util import cleanup_rft_backups, describe_exception, RFT_BACKUP_PATTERN

from Autodesk.Revit.DB import SaveAsOptions, Transaction, FormatOptions, SpecTypeId, UnitTypeId

FOLDER = r"C:\Users\smadera\OneDrive - HLW International LLP\Desktop\FAMILY TEMP"
METRIC_SUFFIX = "_metric"

# Verified against Revit's own shipped Metric templates (Metric Generic
# Model.rft, Metric Furniture.rft, Metric Planting.rft) - Length and
# Distance are deliberately different units in Revit's own convention.
METRIC_UNITS = {
    SpecTypeId.Length:   UnitTypeId.Millimeters,
    SpecTypeId.Area:     UnitTypeId.SquareMeters,
    SpecTypeId.Volume:   UnitTypeId.CubicMeters,
    SpecTypeId.Distance: UnitTypeId.Centimeters,
    SpecTypeId.Angle:    UnitTypeId.Degrees,
    SpecTypeId.Slope:    UnitTypeId.Degrees,
}

uiapp = revit_script_util.GetUIApplication()
app = uiapp.Application

rft_files = sorted(
    os.path.join(FOLDER, f) for f in os.listdir(FOLDER)
    if f.lower().endswith(".rft")
    and not f.lower().endswith(METRIC_SUFFIX + ".rft")
    and not RFT_BACKUP_PATTERN.search(f)
)
Output("Found {} .rft file(s) in {}".format(len(rft_files), FOLDER))

save_as_options = SaveAsOptions()
save_as_options.OverwriteExistingFile = True

succeeded = 0
failed = 0
for path in rft_files:
    base, ext = os.path.splitext(path)
    metric_path = base + METRIC_SUFFIX + ext
    Output("Processing: " + path)
    Output("  -> " + metric_path)

    doc = None
    try:
        doc = app.NewFamilyDocument(path)

        t = Transaction(doc, "Set metric units")
        t.Start()
        units = doc.GetUnits()
        for spec, unit_type in METRIC_UNITS.items():
            units.SetFormatOptions(spec, FormatOptions(unit_type))
        doc.SetUnits(units)
        t.Commit()

        doc.SaveAs(metric_path, save_as_options)
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
