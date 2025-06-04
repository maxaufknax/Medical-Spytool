#!/bin/bash
echo "Starting Medical-Spytool..."
cd "$(dirname "$0")"
python3 run_medical_spytool.py || python run_medical_spytool.py
