---
name: revit-export-setup
description: Guides a user through setting up a new Revit batch export job — defining the job, verifying Revit export settings, extracting cloud model GUIDs from journal files, writing the task script and file list, testing manually, and scheduling on BIMNODE3.
---

You are helping a team member set up a new automated Revit batch export job using RevitBatchProcessor (RBP). Work through the steps below in order, asking questions as needed and doing as much of the work (file reading, script writing) as you can automatically.

---

## STEP 1 — Define the job

Ask the user the following questions before proceeding. Collect all answers before moving on.

1. **Project name** — what is this job called? (Used for folder and file naming, e.g. `Avalon`, `SBO`)
2. **Export types** — DWG, PDF, or both?
3. **Models** — how many Revit files are involved? Are they cloud-hosted (Autodesk Docs / BIM 360) or local files?
4. **Output location** — where should exports be saved? Strongly recommend an **OneDrive path** (e.g. `C:\Users\<name>\OneDrive - HLW International LLP\Desktop\<FolderName>`) so files are accessible on their local machine and not only on BIMNODE3. Do not accept a path under `C:\` that is not OneDrive-synced without flagging this.
5. **Weekly folder pattern** — do exports go into a dated weekly folder (e.g. `2026_0724 - PROJECT - WEEKLY EXPORTS`)? If yes, what is the folder name suffix pattern?
6. **Scheduling** — should this run on a schedule? If yes, what day and time?

---

## STEP 2 — Open the files in Revit and verify export settings

Instruct the user to do the following before writing any scripts. These steps must be done in Revit by the user.

### For every Revit file in the job:

**If exporting DWG:**
- Go to **File → Export → CAD Formats → DWG**
- Confirm a named **Export Setup** exists (dropdown at top of dialog). Note the exact name.
- Confirm a named **View/Sheet Set** (Export List) exists covering the sheets to export. Note the exact name.

**If exporting PDF:**
- Go to **File → Export → PDF**
- Confirm a named **PDF Setup** exists (dropdown). Note the exact name.
- Confirm a named **View/Sheet Set** covering the sheets exists. Note the exact name.

**If there are multiple Revit files in this job:**
- The export setup names and sheet set names **must match exactly** across every file. Check spelling, capitalisation, and spaces carefully. RBP will throw an error if any file is missing a setup by that name.

Ask the user to report back with:
- The exact DWG Export Setup name (if applicable)
- The exact DWG View/Sheet Set name (if applicable)
- The exact PDF Export Setup name (if applicable)
- The exact PDF View/Sheet Set name (if applicable)

---

## STEP 3 — Extract cloud model GUIDs from journal files

*Skip this step if the models are local `.rvt` files — use their file paths directly in the file list instead.*

For cloud-hosted models, RBP needs the **Project GUID** and **Model GUID** for each file. Extract these from Revit's journal files after the user opens each model.

### Instructions for the user:

1. Open each cloud model in Revit one at a time (just open it — no changes needed, close when done).
2. After opening all models, journal files will be in:
   ```
   C:\Users\<username>\AppData\Local\Autodesk\Revit\Autodesk Revit <version>\Journals\
   ```
3. Share the path to that Journals folder (or tell you their Revit version and username).

### What you do:

Once the user provides the journal folder path, read the most recent journal files (sorted by modification time, newest first) and search for lines containing `ProjectId` / `ModelId` / `cloudProjectId` / `cloudModelId`, or patterns matching `[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}` near cloud model path strings.

The file list format required by RBP is:
```
<RevitVersion> <ProjectGUID> <ModelGUID>
```
Example:
```
2026 76bdef77-9851-4e95-b585-4aa13c1c2475 af89de8a-b3ca-41ec-ba35-c7638e3f2d6a
```

One line per model file. The Revit version is the integer year (e.g. `2026`), not a full version string.

---

## STEP 4 — Write the task script and file list

By this point you should have:
- Project name
- Export types, setup names, and sheet set names
- Output folder path(s)
- GUIDs (for cloud models) or file paths (for local models)

### File locations

All job files go in a new subfolder under `task_scripts/`:
```
task_scripts/
    revit_export_util.py          <- shared library, do not modify
    <ProjectName>/
        export_task_<project>.py  <- task script (write this)
        revit_file_list_<project>.txt  <- file list (write this)
        BatchRvt.Settings.json    <- settings export (done after testing)
```

### Writing the task script

Base the script on `task_scripts/export_task_template.py`. The import block at the top must be exactly:

```python
# -*- coding: utf-8 -*-
import os
import sys
import glob
import revit_script_util
from revit_script_util import Output
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(revit_script_util.GetTaskScriptFilePath()))))
import revit_export_util
```

Key `EXPORTS` list options:

```python
# DWG export
{
    "type":                "DWG",
    "setup":               "<exact DWG Export Setup name>",
    "sheet_set":           "<exact View/Sheet Set name>",
    "output":              r"<OneDrive output path>",
    "delete_pcp":          True,          # always True — removes .pcp files Revit generates
    "rename_strip_prefix": "PREFIX_",     # strips a fixed prefix from DWG filenames (optional)
    "rename_regex":        (r'<pattern>', r'<replacement>'),  # regex rename (optional)
}

# PDF export (Revit 2022+ native)
{
    "type":           "PDF",
    "setup":          "<exact PDF Setup name>",
    "sheet_set":      "<exact View/Sheet Set name>",
    "output":         r"<OneDrive output path>",
    "pdf_filename":   "<combined PDF filename, no extension>",  # omit for individual PDFs
    "pdf_individual": True,   # True = one PDF per sheet (omit or False = combined PDF)
    "rename_regex":   (r'<pattern>', r'<replacement>'),  # regex rename on individual PDFs (optional)
}
```

**If the job uses a weekly folder with a glob pattern**, include this block before `EXPORTS`:

```python
DESKTOP = os.path.join(os.environ.get("OneDriveCommercial", os.path.expanduser("~")), "Desktop")
WEEKLY_PATTERN = "* - <PROJECT> - <FOLDER SUFFIX>"

matches = sorted(glob.glob(os.path.join(DESKTOP, WEEKLY_PATTERN)))
if not matches:
    raise Exception("No weekly folder found matching: " + os.path.join(DESKTOP, WEEKLY_PATTERN))
weekly_folder = matches[-1]
Output("Weekly folder: " + weekly_folder)
```

Then reference `weekly_folder` as the output path in EXPORTS.

**If the job clears the output folder before exporting**, add before `run_exports`:

```python
Output("Clearing output folders...")
seen = set()
for cfg in EXPORTS:
    f = cfg["output"]
    if f not in seen:
        seen.add(f)
        revit_export_util.clear_folder_contents(f)
```

**If the weekly folder should be renamed to today's date after exporting**, add after `run_exports`:

```python
Output("Renaming weekly folder...")
revit_export_util.rename_weekly_folder(weekly_folder)
```

End every script with:
```python
Output("Job start: " + revit_script_util.GetRevitFilePath())
revit_export_util.run_exports(doc, uiapp, EXPORTS)
Output("Job complete.")
```

### Writing the file list

For **cloud models**, one line per file:
```
2026 <ProjectGUID> <ModelGUID>
```

For **local files**, one line per file:
```
C:\full\path\to\model.rvt
```

---

## STEP 5 — Test manually

Instruct the user to run the job once from the RBP GUI before scheduling:

1. Open **Revit Batch Processor** from the Start menu
2. Set **Revit File List** → browse to `revit_file_list_<project>.txt`
3. Set **Task Script** → browse to `export_task_<project>.py`
4. Set **Revit Version** → match the version in the file list
5. Set **Worksets** → Close All
6. Click **Start**
7. Watch the log output — confirm each file completes without errors and the output folder contains the expected files

If errors appear, read the log carefully. Common issues:
- `No module named revit_export_util` — the `sys.path` line is wrong; verify the script is in a subfolder of `task_scripts/`
- `View/Sheet Set not found` — name mismatch; re-check the exact name in Revit
- `DWG/PDF Export Setup not found` — name mismatch; re-check the exact name in Revit
- `No weekly folder found` — the glob pattern doesn't match any folder on the Desktop; check the suffix

Once the test passes, export the settings: in RBP, go to **File → Save Settings** and save as `BatchRvt.Settings.json` inside `task_scripts/<ProjectName>/`.

---

## STEP 6 — Schedule on BIMNODE3

BIMNODE3 is the shared remote machine used for all scheduled Revit automation at HLW. Scheduling must be done on that machine.

### Verify BIMNODE3 is ready

Log into BIMNODE3 via Remote Desktop. Then confirm:

1. **The GitHub repo is cloned** — navigate to the same path the scripts use. The expected location is:
   ```
   C:\Users\<your username>\OneDrive - HLW International LLP\Documents\GitHub\RevitBatchProcessor\
   ```
   If it is not there, clone it: open Git Bash or GitHub Desktop and clone the `RevitBatchProcessor` repo to that path.

2. **RevitBatchProcessor is installed** — press `Win + R`, type:
   ```
   %LOCALAPPDATA%\RevitBatchProcessor
   ```
   and hit Enter. You should see `BatchRvt.exe` in that folder. If not, install RBP from the repo's Releases page on GitHub.

3. **Desktop Connector is running and authenticated** — look for the Autodesk Desktop Connector icon in the system tray. It must be signed in with your Autodesk account to access cloud models.

4. **The output path exists** — confirm the OneDrive folder the script outputs to is accessible from BIMNODE3 (it should be if it is a OneDrive path synced to your account).

### Create the scheduled task

1. Press `Win + R`, type `taskschd.msc`, hit Enter
2. Right-click **Task Scheduler Library** → **Create Task** (not Basic Task)
3. **General tab**
   - Name: `Revit Export - <ProjectName>`
   - Select **"Run only when user is logged on"**
   - Check **"Run with highest privileges"**
4. **Triggers tab** → New
   - Begin the task: On a schedule
   - Weekly → select day and time
   - Ensure Enabled is checked → OK
5. **Actions tab** → New
   - Action: Start a program
   - Program/script: `%LOCALAPPDATA%\RevitBatchProcessor\BatchRvt.exe`
   - Add arguments:
     ```
     --settings_file "C:\Users\<username>\OneDrive - HLW International LLP\Documents\GitHub\RevitBatchProcessor\task_scripts\<ProjectName>\BatchRvt.Settings.json"
     ```
6. **Conditions tab**
   - Uncheck "Start the task only if the computer is on AC power"
   - Check **"Wake the computer to run this task"**
7. **Settings tab**
   - Check "If the task is already running, do not start a new instance"
8. Click **OK**

### Keep your session alive on BIMNODE3

The task runs in your user session. After setting up the task:
- **Disconnect** from RDP (do not log out — disconnect only)
- Your session stays alive on the server and the task will fire at the scheduled time
- Desktop Connector continues running in your disconnected session

> **Note:** If IT policy logs out disconnected sessions after a set time, you will need to reconnect before each scheduled run, or ask IT to extend the timeout for your account.

### Test the scheduled task

Right-click the task in Task Scheduler → **Run** to trigger it immediately and confirm it fires correctly without you being actively connected.
