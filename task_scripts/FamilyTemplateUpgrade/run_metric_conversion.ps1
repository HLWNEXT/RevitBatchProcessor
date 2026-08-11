# Family TEMPLATE metric-conversion job
#
# Creates a metric copy of every .rft in $folder (Length -> mm, Area -> m2,
# Volume -> m3), saved alongside the original with a "_metric" suffix, e.g.
# Planting_HLW.rft -> Planting_HLW_metric.rft. Originals are left untouched.
#
# Uses the same throwaway-anchor-project trick as run_family_upgrade.ps1,
# and the same per-version anchor files under .\<year>\_anchor_<yy>.rvt -
# see that script's header comment for one-time setup if a version's anchor
# doesn't exist yet.
#
# Run for Revit 2025 (default):  powershell -ExecutionPolicy Bypass -File run_metric_conversion.ps1
# Run for Revit 2026:            powershell -ExecutionPolicy Bypass -File run_metric_conversion.ps1 -RevitVersion 2026

param(
    [int]$RevitVersion = 2025
)

$folder       = "C:\Users\smadera\OneDrive - HLW International LLP\Desktop\FAMILY TEMP"

$scriptDir    = $PSScriptRoot
$shortYear    = $RevitVersion.ToString().Substring(2)
$yearFolder   = Join-Path $scriptDir $RevitVersion
$taskScript   = Join-Path $scriptDir "convert_to_metric_task.py"
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
    Write-Host "See the ONE-TIME SETUP steps in run_family_upgrade.ps1 to create it for Revit $RevitVersion." -ForegroundColor Yellow
    pause
    exit 1
}

if (-not (Test-Path $folder)) {
    Write-Host "ERROR: Folder not found: $folder" -ForegroundColor Red
    pause
    exit 1
}

$rftCount = (Get-ChildItem $folder -Filter "*.rft" -File | Where-Object { $_.Name -notlike "*_metric.rft" }).Count
if ($rftCount -eq 0) {
    Write-Host "No .rft files found to convert in: $folder" -ForegroundColor Yellow
    pause
    exit 0
}
Write-Host "Found $rftCount .rft file(s) to convert in: $folder" -ForegroundColor Cyan

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
