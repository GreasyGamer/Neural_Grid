@echo off
title NEURAL_GRID v1.0 - Launching...
color 02

set DRIVE=%~d0
set NG_DIR=%DRIVE%\NEURAL_GRID
set PYTHON=%NG_DIR%\WinPython\WPy64-31241\python-3.12.4.amd64\python.exe
set SCRIPT=%NG_DIR%\neural_grid_usbv1.py

if not exist "%PYTHON%" (
    echo.
    echo  [!!] WinPython not found.
    echo  [!!] Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

if not exist "%SCRIPT%" (
    echo.
    echo  [!!] neural_grid_usbv1.py not found in %NG_DIR%
    echo  [!!] Make sure all files are inside the NEURAL_GRID folder.
    echo.
    pause
    exit /b 1
)

"%PYTHON%" "%SCRIPT%"
