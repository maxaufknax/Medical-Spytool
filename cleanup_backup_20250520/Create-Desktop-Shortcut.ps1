# Create-Desktop-Shortcut.ps1
# Erstellt eine Verknüpfung auf dem Desktop zum einfachen Starten der Medical Spytool Anwendung

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Medical Spytool.lnk")
$Shortcut.TargetPath = Join-Path -Path $PSScriptRoot -ChildPath "RunMedicalSpytool.bat"
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = Join-Path -Path $PSScriptRoot -ChildPath "generated-icon.png"
$Shortcut.Description = "Startet die Medical Spytool Anwendung"
$Shortcut.Save()

Write-Host ""
Write-Host "============================================" -ForegroundColor Blue
Write-Host "  Desktop-Verknüpfung wurde erstellt!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Sie können die Anwendung jetzt durch Doppelklick auf das" -ForegroundColor Cyan
Write-Host "Symbol 'Medical Spytool' auf Ihrem Desktop starten." -ForegroundColor Cyan
Write-Host ""
Write-Host "Die Anwendung wird sich automatisch im Browser öffnen." -ForegroundColor Cyan
