#!/bin/bash
# MedicalSpy Start Script for Unix/Linux/MacOS
# This script now delegates to manage.py

echo "============================================"
echo "  Medical Spytool - Wissenschaftliches Publikations-Suchwerkzeug"
echo "============================================"
echo ""

# Set base directory to the script's directory
BASE_DIR=$(dirname "$0")
cd "$BASE_DIR" || exit

echo "Running setup via manage.py..."
# Attempt to use python3 first, then python
if command -v python3 &>/dev/null; then
    PYTHON_EXEC=python3
elif command -v python &>/dev/null; then
    PYTHON_EXEC=python
else
    echo "Python not found. Please install Python 3.8 or higher."
    exit 1
fi

$PYTHON_EXEC manage.py setup --full

if [ $? -ne 0 ]; then
  echo ""
  echo "Setup via manage.py failed. Please check the output above."
  read -p "Press Enter to exit"
  exit 1
fi

echo "Starting MedicalSpy application via manage.py..."
echo ""
echo "The application will be accessible at: http://localhost:5000 (or the port specified in .env/arguments)"
echo "Press CTRL+C to stop the application."
echo ""

$PYTHON_EXEC manage.py run --open-browser # Add other arguments as needed, e.g., --port 5001

if [ $? -ne 0 ]; then
  echo ""
  echo "Failed to start the application via manage.py. Please check the output above."
  read -p "Press Enter to exit"
fi
