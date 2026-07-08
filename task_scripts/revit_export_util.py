"""
Shared utility for Revit DWG and PDF batch exports via RevitBatchProcessor.
Place in the same folder as all job task scripts so Python can import it.
"""
import os
import clr
from System.Collections.Generic import List

clr.AddReference("RevitAPI")
from Autodesk.Revit.DB import (
    FilteredElementCollector, ViewSheetSet, ElementId,
    ExportDWGSettings,
)

from revit_script_util import Output


def get_view_ids(doc, set_name):
    """Return a .NET List[ElementId] for a named ViewSheetSet stored in the document."""
    for vss in FilteredElementCollector(doc).OfClass(ViewSheetSet):
        if vss.Name == set_name:
            return List[ElementId]([v.Id for v in vss.Views])
    raise Exception("View/Sheet Set not found in document: '{}'".format(set_name))


def export_dwg(doc, setup_name, sheet_set_name, output_folder):
    """Export DWG using a named ExportDWGSettings and a named ViewSheetSet."""
    settings = ExportDWGSettings.FindByName(doc, setup_name)
    if settings is None:
        raise Exception("DWG Export Setup not found: '{}'".format(setup_name))
    options  = settings.GetDWGExportOptions()
    view_ids = get_view_ids(doc, sheet_set_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    doc.Export(output_folder, "", view_ids, options)
    Output("  DWG done -> " + output_folder)


def export_pdf_native(doc, setup_name, sheet_set_name, output_folder, pdf_filename=None):
    """Export PDF using Revit 2022+ native ExportPDFSettings."""
    from Autodesk.Revit.DB import ExportPDFSettings
    settings = ExportPDFSettings.FindByName(doc, setup_name)
    if settings is None:
        raise Exception("PDF Export Setup not found: '{}'".format(setup_name))
    options  = settings.GetOptions()
    if pdf_filename:
        options.FileName = pdf_filename
    view_ids = get_view_ids(doc, sheet_set_name)
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    doc.Export(output_folder, view_ids, options)
    Output("  PDF done -> " + output_folder)


def export_pdf_print(doc, sheet_set_name, output_folder, pdf_filename=None,
                     pdf_printer="Microsoft Print to PDF"):
    """Export PDF via PrintManager (Revit < 2022 fallback)."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    out_name = (pdf_filename or "export") + ".pdf"
    pm = doc.PrintManager
    pm.SelectNewPrintDriver(pdf_printer)
    pm.PrintToFile    = True
    pm.CombinedFile   = True
    pm.PrintToFileName = os.path.join(output_folder, out_name)
    pm.ViewSheetSetting.CurrentViewSheetSet = next(
        vss for vss in FilteredElementCollector(doc).OfClass(ViewSheetSet)
        if vss.Name == sheet_set_name
    )
    pm.Apply()
    pm.SubmitPrint()
    Output("  PDF done (PrintManager) -> " + output_folder)


def post_process_dwg_folder(folder, strip_before_A=False, delete_pcp=False,
                            rename_strip_prefix=None):
    """
    Optional post-processing on exported DWG files.

    delete_pcp          Delete the .pcp plotter config files Revit generates alongside DWGs.

    rename_strip_prefix Find this string in the filename, keep everything from that point,
                        and replace ' - ' with '-'.
                        e.g. prefix="US-SBO-F0K1_"
                             "A_detached-Floor Plan - US-SBO-F0K1_A - PLAN - EXPORT - L1.dwg"
                          -> "A-PLAN-EXPORT-L1.dwg"

    strip_before_A      Simpler fallback: remove everything before the first 'A'.
                        e.g. "20241115 - A100 Floor Plan.dwg" -> "A100 Floor Plan.dwg"
                        Not used when rename_strip_prefix is set.
    """
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)

        if delete_pcp and filename.lower().endswith(".pcp"):
            os.remove(filepath)
            Output("  Deleted: " + filename)
            continue

        if not filename.lower().endswith(".dwg"):
            continue

        base = filename[:-4]  # strip .dwg extension

        if rename_strip_prefix:
            idx = base.rfind(rename_strip_prefix)  # rfind = last occurrence, handles prefix appearing twice
            if idx >= 0:
                remainder = base[idx + len(rename_strip_prefix):]  # e.g. "A - PLAN - EXPORT - L1"
                new_name  = remainder.replace(" - ", "-") + ".dwg"  # "A-PLAN-EXPORT-L1.dwg"
                new_path  = os.path.join(folder, new_name)
                if not os.path.exists(new_path):
                    os.rename(filepath, new_path)
                    Output("  Renamed: {} -> {}".format(filename, new_name))
            else:
                Output("  WARNING: prefix '{}' not found in '{}'".format(rename_strip_prefix, filename))

        elif strip_before_A:
            idx = base.find("A")
            if idx > 0:
                new_name = base[idx:] + ".dwg"
                new_path = os.path.join(folder, new_name)
                if not os.path.exists(new_path):
                    os.rename(filepath, new_path)
                    Output("  Renamed: {} -> {}".format(filename, new_name))


def cleanup_revit_backups(revit_file_path):
    """
    Delete Revit backup files and backup subfolders that Revit creates in the same
    folder as the source file when detaching or opening a workshared model.
    Covers both the host model and any linked files.

    Revit typically creates:
      - A subfolder named  <ModelName>_backup/  containing numbered .rvt/.rfa files
      - Loose backup files <ModelName>.XXXX.rvt  in the same directory
    """
    import re
    import shutil
    import stat
    import subprocess
    folder = os.path.dirname(revit_file_path)
    backup_file_pattern   = re.compile(r'\.\d{4}\.(rvt|rfa)$', re.IGNORECASE)
    backup_folder_pattern = re.compile(r'(_backup$|^Revit_temp$)', re.IGNORECASE)
    deleted_files = 0
    deleted_dirs  = 0

    def force_remove_readonly(func, path, _):
        """Error handler for shutil.rmtree: clear read-only flag then retry."""
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def force_delete_folder(full_path, entry):
        try:
            shutil.rmtree(full_path, onerror=force_remove_readonly)
            return True
        except OSError:
            pass
        # Fallback: use Windows rd command to bypass OneDrive/permission restrictions
        try:
            result = subprocess.call(
                ['cmd', '/c', 'rd', '/s', '/q', full_path],
                stdout=open(os.devnull, 'w'), stderr=open(os.devnull, 'w')
            )
            return result == 0
        except OSError:
            return False

    for entry in os.listdir(folder):
        full_path = os.path.join(folder, entry)
        if os.path.isdir(full_path) and backup_folder_pattern.search(entry):
            if force_delete_folder(full_path, entry):
                Output("  Deleted backup folder: " + entry)
                deleted_dirs += 1
            else:
                Output("  WARNING: could not delete folder: " + entry)
        elif os.path.isfile(full_path) and backup_file_pattern.search(entry):
            try:
                os.chmod(full_path, stat.S_IWRITE)
                os.remove(full_path)
                Output("  Deleted backup file: " + entry)
                deleted_files += 1
            except OSError as e:
                Output("  WARNING: could not delete {}: {}".format(entry, str(e)))

    if deleted_files == 0 and deleted_dirs == 0:
        Output("  No Revit backup files found in: " + folder)
    else:
        Output("  Deleted {} backup folder(s) and {} backup file(s) from: {}".format(
            deleted_dirs, deleted_files, folder))


def rename_weekly_folder(folder_path):
    """
    Rename a weekly folder so its date prefix reflects today's date.

    Expects the folder name to contain ' - ' separating a date prefix from
    the rest of the name, e.g.:
      "2026_0630 - SBO-P1-CS - WEEKLY UPLOAD"
      ->  "2026_0707 - SBO-P1-CS - WEEKLY UPLOAD"

    Uses Shell.Application COM (via PowerShell subprocess) so that Windows
    fires the shell change notification and Quick Access pins update automatically.
    Falls back to os.rename() if the shell rename fails.
    """
    from datetime import date
    import subprocess
    parent      = os.path.dirname(folder_path)
    folder_name = os.path.basename(folder_path)
    separator   = " - "
    idx         = folder_name.find(separator)
    if idx < 0:
        Output("  WARNING: could not rename weekly folder - no ' - ' separator found in: " + folder_name)
        return
    suffix    = folder_name[idx + len(separator):]
    today_str = date.today().strftime("%Y_%m%d")
    new_name  = today_str + separator + suffix
    new_path  = os.path.join(parent, new_name)
    if folder_path == new_path:
        Output("  Weekly folder already has today's date: " + folder_name)
        return

    # Rename via Shell.Application so Explorer fires SHChangeNotify and
    # Quick Access pins update. os.rename() bypasses the shell and breaks pins.
    p = parent.replace("'", "''")
    o = folder_name.replace("'", "''")
    n = new_name.replace("'", "''")
    ps = (
        "$sh = New-Object -ComObject Shell.Application;"
        "$ns = $sh.Namespace('{p}');"
        "$it = $ns.ParseName('{o}');"
        "if ($it) {{ $it.Name = '{n}' }} else {{ exit 1 }}"
    ).format(p=p, o=o, n=n)

    result = subprocess.call(
        ['powershell', '-NoProfile', '-Command', ps],
        stdout=open(os.devnull, 'w'),
        stderr=open(os.devnull, 'w'),
    )
    if result == 0:
        Output("  Renamed weekly folder: {} -> {}".format(folder_name, new_name))
    else:
        os.rename(folder_path, new_path)
        Output("  Renamed weekly folder (pin may need refresh): {} -> {}".format(folder_name, new_name))


def clear_folder_contents(folder):
    """Delete all files and subfolders inside folder without removing the folder itself."""
    import shutil, stat
    if not os.path.exists(folder):
        return

    def force_remove_readonly(func, path, _):
        os.chmod(path, stat.S_IWRITE)
        func(path)

    for entry in os.listdir(folder):
        full_path = os.path.join(folder, entry)
        try:
            if os.path.isfile(full_path):
                os.chmod(full_path, stat.S_IWRITE)
                os.remove(full_path)
            elif os.path.isdir(full_path):
                shutil.rmtree(full_path, onerror=force_remove_readonly)
        except OSError as e:
            Output("  WARNING: could not delete {}: {}".format(entry, str(e)))
    Output("  Cleared folder: " + folder)


def resolve_output_folder(base_folder, date_subfolder=False):
    """Optionally append a YYYY-MM-DD subfolder so each run goes to its own directory."""
    if date_subfolder:
        from datetime import date
        base_folder = os.path.join(base_folder, date.today().isoformat())
    return base_folder


def run_exports(doc, uiapp, exports):
    """
    Run a list of export configs sequentially against an already-open document.

    Each entry in `exports` is a dict with these keys:

        type            "DWG" or "PDF"
        setup           Name of the export setup saved in the Revit document
        sheet_set       Name of the View/Sheet Set saved in the Revit document
        output          Absolute path to the base output folder

    Optional keys:

        date_subfolder       bool  Append YYYY-MM-DD subfolder (default False)
        pdf_filename         str   Filename for combined PDF, no extension (PDF only)
        rename_strip_prefix  str   Find this prefix in DWG filenames, keep from that point,
                                   replace ' - ' with '-'.
                                   e.g. "US-SBO-F0K1_" turns
                                   "A_detached-Floor Plan - US-SBO-F0K1_A - PLAN - EXPORT - L1.dwg"
                                   into "A-PLAN-EXPORT-L1.dwg"  (DWG only)
        strip_before_A       bool  Simpler rename: strip everything before first 'A' (DWG only)
        delete_pcp           bool  Delete .pcp files generated during DWG export (DWG only)
    """
    revit_version = int(uiapp.Application.VersionNumber)
    for cfg in exports:
        Output("Exporting: [{type}] setup='{setup}' sheets='{sheet_set}'".format(**cfg))
        folder = resolve_output_folder(cfg["output"], cfg.get("date_subfolder", False))
        if cfg["type"] == "DWG":
            export_dwg(doc, cfg["setup"], cfg["sheet_set"], folder)
            post_process_dwg_folder(
                folder,
                rename_strip_prefix=cfg.get("rename_strip_prefix"),
                strip_before_A=cfg.get("strip_before_A", False),
                delete_pcp=cfg.get("delete_pcp", False),
            )
        elif cfg["type"] == "PDF":
            pdf_fn = cfg.get("pdf_filename")
            if revit_version >= 2022:
                export_pdf_native(doc, cfg["setup"], cfg["sheet_set"], folder, pdf_filename=pdf_fn)
            else:
                export_pdf_print(doc, cfg["sheet_set"], folder, pdf_filename=pdf_fn)
        else:
            raise Exception("Unknown export type: " + cfg["type"])
