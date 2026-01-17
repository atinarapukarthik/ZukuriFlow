@echo off
REM ZukuriFlow Elite - Quick Start Script for Windows

echo =====================================
echo ZukuriFlow Elite - Setup
echo =====================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
echo.

echo =====================================
echo Setup complete!
echo =====================================
echo.
echo To run ZukuriFlow Elite:
echo   python src\zukuriflow_elite.py
echo.
pause
