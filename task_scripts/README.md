# Revit Batch Export — Task Scripts

This folder contains all automated export jobs set up for HLW projects using [RevitBatchProcessor](https://github.com/bvn-architecture/RevitBatchProcessor) (RBP). Each job opens one or more cloud-hosted Revit files, runs DWG and/or PDF exports using named presets saved in those files, performs post-processing (renaming, cleanup), and optionally renames a weekly output folder.

---

## Folder Structure

```
task_scripts/
    revit_export_util.py          Shared export library — do not modify
    export_task_template.py       Starting point for new jobs
    README.md                     This file

    Avalon/
        export_task_avalon.py     Task script for Project Avalon
        revit_file_list_avalon.txt   Cloud model GUIDs (6 buildings)
        BatchRvt.Settings.json    RBP settings file for scheduling

    SBO/
        export_task_sbo.py        Task script for SBO-P1-CS
        revit_file_list_sbo.txt   Cloud model GUID
        BatchRvt.Settings.json    RBP settings file for scheduling
```

Each project lives in its own subfolder. The shared library (`revit_export_util.py`) stays in the root and is never modified — all project-specific configuration lives in the task script.

---

## Setting Up a New Export Job

**Use the Claude skill.** If you have Claude Code installed, run:

```
/revit-export-setup
```

Claude will walk you through the entire process interactively:

1. Defining the job (project, export types, output locations)
2. Verifying export settings in Revit
3. Extracting cloud model GUIDs from Revit journal files automatically
4. Writing the task script and file list for you
5. Testing the job manually in the RBP GUI
6. Scheduling it on BIMNODE3

You do not need to write any code yourself — just answer Claude's questions and verify the outputs.

> **Prerequisite:** Clone this repository to your machine before invoking the skill. The path should be:
> `C:\Users\<your username>\OneDrive - HLW International LLP\Documents\GitHub\RevitBatchProcessor`
> Using the OneDrive path ensures the same path resolves on both your local machine and BIMNODE3.

---

## Output Folder Convention

Export outputs should always go to **OneDrive-synced paths** (e.g. your OneDrive Desktop), not to local folders on BIMNODE3. This ensures:
- You can access the files on your own machine without logging into BIMNODE3
- Files are backed up and synced automatically

Weekly output folders follow the naming pattern:
```
2026_0724 - PROJECT NAME - WEEKLY EXPORTS
```
Scripts locate the current week's folder automatically using a glob pattern — you rename or create the folder each week and the script picks it up.

---

## Scheduling

All scheduled jobs run on **BIMNODE3**, the shared remote machine dedicated to Revit automation. See the skill (`/revit-export-setup`, Step 6) for full setup instructions.

To check what is currently scheduled, log into BIMNODE3 and open Task Scheduler (`taskschd.msc`).

---

## How It Works

Each job follows this pattern at runtime:

1. RBP opens each Revit file in the file list (cloud or local)
2. The task script runs once per file
3. The script exports DWG and/or PDF using named presets saved inside the Revit file
4. Post-processing runs: `.pcp` files are deleted, filenames are cleaned up
5. If configured: the output folder is cleared of last week's files before the first file runs
6. If configured: the weekly folder is renamed to today's date after all files complete

---

## Troubleshooting

| Error | Likely cause |
|---|---|
| `No module named revit_export_util` | Script is in a subfolder but the `sys.path` line is missing or wrong |
| `View/Sheet Set not found: 'X'` | The sheet set name in the script doesn't exactly match the name saved in Revit |
| `DWG/PDF Export Setup not found: 'X'` | The export setup name doesn't exactly match — check capitalisation and spaces |
| `No weekly folder found matching: ...` | No folder on the Desktop matches the glob pattern — check the folder exists and the suffix matches |
| Export returns `False` / empty output | A Revit dialog was shown and dismissed during export — check the RBP log for dialog names |

For anything else, check the RBP log file at:
```
C:\Users\<username>\AppData\Local\BatchRvt\
```
