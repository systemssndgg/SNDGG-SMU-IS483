@echo off
echo Activating virtual environment...
echo call myenv\Scripts\activate

echo Running Python script...
python import_ura_parking.py
python import_weather.py

pause
