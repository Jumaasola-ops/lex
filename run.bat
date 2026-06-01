@echo off
REM Android Security Scanner - Windows Batch Script
REM Usage: run.bat [command] [arguments]

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
    echo Installing dependencies...
    call venv\Scripts\pip install -r requirements.txt
    echo.
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the scanner
python main.py %*

REM Deactivate virtual environment
deactivate
