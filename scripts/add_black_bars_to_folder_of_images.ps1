param(
    [string]$ImagesFolder,
    [string]$ConfigPath = "config.json",
    [string]$Color = "0,0,0"
)

# If folder was not passed, open a folder picker
if (-not $ImagesFolder) {
    Add-Type -AssemblyName System.Windows.Forms

    $dlg = New-Object System.Windows.Forms.FolderBrowserDialog
    $dlg.Description = "Select folder with images"
    $dlg.ShowNewFolderButton = $true

    if ($dlg.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        $ImagesFolder = $dlg.SelectedPath
    } else {
        Write-Host "No folder selected. Exiting."
        exit 1
    }
}

Write-Host "Using folder: $ImagesFolder"

# Call the Python script; adjust 'python' path if needed
cd ..
python "tools/add_black_bars_to_images.py" "$ImagesFolder" "$ConfigPath" "$Color"
