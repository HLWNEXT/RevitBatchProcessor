# -*- coding: utf-8 -*-
"""
Shared utility for the family template batch jobs (upgrade and metric
conversion). Place in the same folder as those task scripts - do not modify
without checking both callers.
"""
import os
import re

from revit_script_util import Output

RFT_BACKUP_PATTERN = re.compile(r'\.\d{4}\.rft$', re.IGNORECASE)


def cleanup_rft_backups(folder):
    """Delete numbered backup files Revit creates alongside .rft saves, e.g. Planting_HLW.0001.rft"""
    deleted = 0
    for filename in os.listdir(folder):
        if RFT_BACKUP_PATTERN.search(filename):
            filepath = os.path.join(folder, filename)
            try:
                os.remove(filepath)
                Output("  Deleted backup: " + filename)
                deleted += 1
            except OSError as e:
                Output("  WARNING: could not delete backup {}: {}".format(filename, str(e)))
    if deleted == 0:
        Output("  No .rft backup files found in: " + folder)
    else:
        Output("  Deleted {} .rft backup file(s) from: {}".format(deleted, folder))


def describe_exception(e):
    """Format an exception with its full .NET InnerException chain for logging."""
    parts = [type(e).__name__ + ": " + str(e)]
    inner = getattr(e, "InnerException", None)
    while inner is not None:
        parts.append("  caused by " + type(inner).__name__ + ": " + str(inner.Message))
        inner = getattr(inner, "InnerException", None)
    return " | ".join(parts)
