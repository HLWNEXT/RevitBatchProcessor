# Avalon weekly export post-processing
# Run this after manually exporting DWG + PDF from all 6 buildings.
# - Deletes .pcp files
# - Renames DWG files:  "Project Avalon_Building 20_AI_26-Sheet - A-060-1 - OVERALL SLAB PLANS - BUILDING 20.dwg"
#                    -> "A-060 - OVERALL SLAB PLANS - BUILDING 20.dwg"
# - Renames PDF files:  "A-060.1 - OVERALL SLAB PLANS - BUILDING 27.pdf"
#                    -> "A-060 - OVERALL SLAB PLANS - BUILDING 27.pdf"
# - Renames the weekly folder to today's date (Quick Access pin safe)

$desktop = "$env:USERPROFILE\OneDrive - HLW International LLP\Desktop"
$pattern = "*- AVALON - CAD AND PDF BACKGROUNDS"

$folder = Get-ChildItem $desktop -Directory -Filter $pattern | Sort-Object Name | Select-Object -Last 1

if (-not $folder) {
    Write-Host "ERROR: No folder matching '$pattern' found on Desktop." -ForegroundColor Red
    pause
    exit 1
}

Write-Host "Folder: $($folder.FullName)" -ForegroundColor Cyan

# --- Delete .pcp files ---
$pcpFiles = Get-ChildItem $folder.FullName -Filter "*.pcp"
foreach ($f in $pcpFiles) {
    Remove-Item $f.FullName -Force
    Write-Host "  Deleted: $($f.Name)"
}

# --- Rename DWG files ---
# Input:  "Project Avalon_Building 20_AI_26-Sheet - A-060-1 - OVERALL SLAB PLANS - BUILDING 20.dwg"
# Output: "A-060 - OVERALL SLAB PLANS - BUILDING 20.dwg"
$dwgFiles = Get-ChildItem $folder.FullName -Filter "*.dwg"
foreach ($f in $dwgFiles) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
    $newBase = $base -replace '^.*Sheet - (A-[A-Z0-9]+)-\d+( - .+)$', '$1$2'
    if ($newBase -ne $base) {
        $newName = $newBase + ".dwg"
        Rename-Item $f.FullName $newName
        Write-Host "  DWG: $($f.Name) -> $newName"
    } else {
        Write-Host "  WARNING: DWG regex did not match '$($f.Name)'" -ForegroundColor Yellow
    }
}

# --- Rename PDF files ---
# Input:  "A-060.1 - OVERALL SLAB PLANS - BUILDING 27.pdf"
# Output: "A-060 - OVERALL SLAB PLANS - BUILDING 27.pdf"
$pdfFiles = Get-ChildItem $folder.FullName -Filter "*.pdf"
foreach ($f in $pdfFiles) {
    $base = [System.IO.Path]::GetFileNameWithoutExtension($f.Name)
    $newBase = $base -replace '^(A-[A-Z0-9]+)\.\d+( - .+)$', '$1$2'
    if ($newBase -ne $base) {
        $newName = $newBase + ".pdf"
        Rename-Item $f.FullName $newName
        Write-Host "  PDF: $($f.Name) -> $newName"
    } else {
        Write-Host "  WARNING: PDF regex did not match '$($f.Name)'" -ForegroundColor Yellow
    }
}

# --- Rename weekly folder (Shell.Application keeps Quick Access pins intact) ---
$today    = Get-Date -Format "yyyy_MMdd"
$oldName  = $folder.Name
$suffix   = ($oldName -split ' - ', 2)[1]   # everything after the first " - "
$newFolderName = "$today - $suffix"

if ($oldName -eq $newFolderName) {
    Write-Host "Folder already has today's date: $oldName" -ForegroundColor Green
} else {
    $sh = New-Object -ComObject Shell.Application
    # Close any Explorer windows navigated into this folder
    foreach ($win in @($sh.Windows())) {
        try { if ($win.Document.Folder.Self.Path -eq $folder.FullName) { $win.Quit() } } catch {}
    }
    Start-Sleep -Milliseconds 400
    $ns = $sh.Namespace($desktop)
    $it = $ns.ParseName($oldName)
    if ($it) {
        $it.Name = $newFolderName
        Write-Host "Renamed folder: $oldName -> $newFolderName" -ForegroundColor Green
    } else {
        # Fallback
        Rename-Item $folder.FullName $newFolderName
        Write-Host "Renamed folder (pin may need refresh): $oldName -> $newFolderName" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Done." -ForegroundColor Green
pause
