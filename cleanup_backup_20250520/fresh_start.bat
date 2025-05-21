@echo off
rem Medical Spytool Fresh Database Creator and Launcher

echo.
echo ====================================================================
echo                 MEDICAL SPYTOOL - FRESH DATABASE
echo ====================================================================
echo.

rem Create instance directory if it doesn't exist
if not exist instance (
    echo Creating instance directory...
    mkdir instance
    echo Instance directory created.
) else (
    echo Instance directory already exists.
)

rem Delete existing database if it exists
if exist instance\medicalspy.db (
    echo Backing up existing database...
    if not exist backups (
        mkdir backups
        echo Backup directory created.
    )
    copy instance\medicalspy.db backups\medicalspy_backup_%date:~-4,4%%date:~-7,2%%date:~-10,2%.db
    echo Backup created.
    echo Removing old database...
    del instance\medicalspy.db
    echo Old database removed.
)

echo Setting environment variables...
set DATABASE_URL=sqlite:///instance/medicalspy.db
echo DATABASE_URL set to: %DATABASE_URL%

rem Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated.

echo.
echo Creating new database...
python db_repair.py
echo Database repair script completed.
pause

echo.
echo Fixing template issues...
python fix_templates.py
echo Template fix script completed.
pause

echo.
echo Fixing models.py...
python fix_jsontype.py
echo Model fix script completed.
pause

echo.
echo Starting application...
python run_fixed.py
echo Application terminated.

pause
