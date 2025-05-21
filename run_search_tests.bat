@echo off
echo ======================================================
echo Medical Spytool - Testing Search Functionality
echo ======================================================
echo.
echo This script will:
echo 1. Reset the database to a clean state
echo 2. Start the Flask application in the background
echo 3. Run the search functionality tests
echo 4. Stop the Flask application
echo.
echo Press Ctrl+C to cancel or any key to continue...
pause > nul

REM Reset the database
echo.
echo Resetting database...
python reset_db_fixed.py
if %ERRORLEVEL% NEQ 0 (
    echo Failed to reset database!
    exit /b 1
)

REM Start the Flask application in the background
echo.
echo Starting Flask application in the background...
start /B python simple_starter.py > flask_output.log 2>&1
echo Waiting for Flask to initialize...
timeout /t 5 > nul

REM Run the database connector tests
echo.
echo Running DNB connector test...
python test_dnb_connector.py
set DNB_TEST_RESULT=%ERRORLEVEL%
echo.

REM Run the search functionality tests
echo.
echo Running search functionality tests...
python test_search_functionality.py
set SEARCH_TEST_RESULT=%ERRORLEVEL%

REM Determine overall test result
if %DNB_TEST_RESULT% EQU 0 (
    if %SEARCH_TEST_RESULT% EQU 0 (
        set TEST_RESULT=0
    ) else (
        set TEST_RESULT=%SEARCH_TEST_RESULT%
    )
) else (
    set TEST_RESULT=%DNB_TEST_RESULT%
)

REM Stop the Flask application
echo.
echo Stopping Flask application...
for /f "tokens=2" %%a in ('tasklist ^| findstr python') do (
    taskkill /PID %%a /F > nul 2>&1
)

REM Show test results
echo.
echo Flask application logs:
type flask_output.log
echo.

if %TEST_RESULT% EQU 0 (
    echo ======================================================
    echo TEST PASSED - Search functionality is working correctly
    echo ======================================================
) else (
    echo ======================================================
    echo TEST FAILED - Search functionality has issues
    echo ======================================================
)

exit /b %TEST_RESULT%
