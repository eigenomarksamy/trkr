@echo off
REM Navigate to the script directory (if the batch script is run from another location)
cd /d "%~dp0"

REM Activate the virtual environment
call .venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install required dependencies
python -m pip install -r requirements.txt

REM Run the Python script
python run.py --cfg config/cfg_bat.yml

REM (Optional) Deactivate the virtual environment
deactivate
