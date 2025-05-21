@echo off
echo Starting Medical Spytool...
cd /d %~dp0
python direct_launcher.py > app_output.log 2>&1
echo Server started. Check app_output.log for details.
