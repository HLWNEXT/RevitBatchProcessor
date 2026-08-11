# Family TEMPLATE (.rft) upgrade job
#
# RevitBatchProcessor's file list can only open real project/family files
# (.rvt/.rfa), not family templates (.rft) - Revit rejects those even if
# renamed. So this script gives RBP one blank throwaway project to open
# (just to launch Revit and fire the task script once); the task script
# itself then loops over every .rft in $folder using the correct
# NewFamilyDocument() API and saves each one back in place.
#
# This job is shared across Revit versions. Version-specific files (just the
# anchor project) live in a subfolder per year, e.g. .\2025\_anchor_25.rvt,
# .\2026\_anchor_26.rvt. Add a new year's subfolder the first time you run
# against that version - see ONE-TIME SETUP below.
#
# ONE-TIME SETUP for a new Revit version (e.g. 2026):
#   1. Create the subfolder: .\2026\
#   2. Open Revit 2026
#   3. File > New > Project > OK (accept the default template)
#   4. File > Save As > Project, save it to:
#        task_scripts\FamilyTemplateUpgrade\2026\_anchor_26.rvt
#   5. Close Revit
#
# Run for Revit 2025 (default):  powershell -ExecutionPolicy Bypass -File run_family_upgrade.ps1
# Run for Revit 2026:            powershell -ExecutionPolicy Bypass -File run_family_upgrade.ps1 -RevitVersion 2026

param(
    [int]$RevitVersion = 2025
)

$folder       = "C:\Users\smadera\OneDrive - HLW International LLP\Desktop\FAMILY TEMP"

$scriptDir    = $PSScriptRoot
$shortYear    = $RevitVersion.ToString().Substring(2)
$yearFolder   = Join-Path $scriptDir $RevitVersion
$taskScript   = Join-Path $scriptDir "upgrade_families_task.py"
$fileListPath = Join-Path $yearFolder "revit_file_list.txt"
$anchorRvt    = Join-Path $yearFolder "_anchor_$shortYear.rvt"
$batchRvtExe  = "$env:LOCALAPPDATA\RevitBatchProcessor\BatchRvt.exe"

if (-not (Test-Path $batchRvtExe)) {
    Write-Host "ERROR: BatchRvt.exe not found at $batchRvtExe" -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path $anchorRvt)) {
    Write-Host "ERROR: Anchor project not found at $anchorRvt" -ForegroundColor Red
    Write-Host "See the ONE-TIME SETUP steps at the top of this script to create it for Revit $RevitVersion." -ForegroundColor Yellow
    pause
    exit 1
}

if (-not (Test-Path $folder)) {
    Write-Host "ERROR: Folder not found: $folder" -ForegroundColor Red
    pause
    exit 1
}

$rftCount = (Get-ChildItem $folder -Filter "*.rft" -File).Count
if ($rftCount -eq 0) {
    Write-Host "No .rft files found in: $folder" -ForegroundColor Yellow
    pause
    exit 0
}
Write-Host "Found $rftCount .rft file(s) in: $folder" -ForegroundColor Cyan

# --- File list has just the anchor project; the task script does the real work ---
Set-Content -Path $fileListPath -Value $anchorRvt -Encoding UTF8

Write-Host "Running RevitBatchProcessor (Revit $RevitVersion)..." -ForegroundColor Cyan
& $batchRvtExe --task_script $taskScript --file_list $fileListPath --revit_version $RevitVersion
$rbpExitCode = $LASTEXITCODE
if ($rbpExitCode -ne 0) {
    Write-Host "WARNING: BatchRvt.exe exited with code $rbpExitCode - check the log." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Done. Check the RBP log output above for per-file OK/ERROR results." -ForegroundColor Green
pause
