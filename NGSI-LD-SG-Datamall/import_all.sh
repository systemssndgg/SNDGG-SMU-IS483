#!/bin/bash
echo "Activating virtual environment..."
source myenv/bin/activate

echo "Running Python script..."
python import_ura_parking.py
python import_weather.py

read -p "Press any key to continue..."