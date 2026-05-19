@echo off
title NEURAL_GRID v1.0 - Setup
color 02
cls

echo.
echo  +===========================================================+
echo  ^|           NEURAL_GRID SETUP v1.0                         ^|
echo  ^|           Portable Offline AI Assistant                   ^|
echo  +===========================================================+
echo.
echo  Initializing setup sequence...
echo.
timeout /t 1 /nobreak >nul

:: ── Paths ───────────────────────────────────────────────────────
set DRIVE=%~d0
set NG_DIR=%DRIVE%\NEURAL_GRID
set WINPYTHON_DIR=%NG_DIR%\WinPython
set PYTHON=%NG_DIR%\WinPython\WPy64-31241\python-3.12.4.amd64\python.exe
set PIP=%NG_DIR%\WinPython\WPy64-31241\python-3.12.4.amd64\Scripts\pip.exe
set MODELS_DIR=%NG_DIR%\models
set LOGS_DIR=%NG_DIR%\chatlogs

echo  +-----------------------------------------------------------+
echo  ^|  STEP 1 - CREATING NEURAL_GRID FOLDER STRUCTURE           ^|
echo  +-----------------------------------------------------------+
echo.

if not exist "%NG_DIR%" (
    mkdir "%NG_DIR%"
    echo  [OK] Created: %NG_DIR%
) else (
    echo  [OK] NEURAL_GRID folder exists: %NG_DIR%
)

if not exist "%MODELS_DIR%" (
    mkdir "%MODELS_DIR%"
    echo  [OK] Created: %MODELS_DIR%
) else (
    echo  [OK] Models folder exists: %MODELS_DIR%
)

if not exist "%LOGS_DIR%" (
    mkdir "%LOGS_DIR%"
    echo  [OK] Created: %LOGS_DIR%
) else (
    echo  [OK] Chatlogs folder exists: %LOGS_DIR%
)

echo.
echo  Your USB structure:
echo.
echo    %DRIVE%\
echo    └── NEURAL_GRID\
echo        ├── launch.bat
echo        ├── neural_grid_usbv6.py
echo        ├── neural_grid_pong.py
echo        ├── WinPython\
echo        ├── models\
echo        └── chatlogs\
echo.

echo  +-----------------------------------------------------------+
echo  ^|  STEP 2 - CHECKING WINPYTHON                              ^|
echo  +-----------------------------------------------------------+
echo.

if exist "%PYTHON%" (
    echo  [OK] WinPython found.
) else (
    echo  [!!] WinPython NOT found.
    echo.
    echo  Please do the following:
    echo.
    echo    1. Go to: https://winpython.github.io/
    echo    2. Download WinPython 3.12 ^(WPy64-31241^)
    echo    3. Extract it into your NEURAL_GRID folder at:
    echo       %WINPYTHON_DIR%\
    echo    4. Re-run this setup script
    echo.
    echo  Opening WinPython download page in your browser...
    timeout /t 2 /nobreak >nul
    start https://winpython.github.io/
    echo.
    pause
    exit /b 1
)

echo.
echo  +-----------------------------------------------------------+
echo  ^|  STEP 3 - INSTALLING DEPENDENCIES                         ^|
echo  +-----------------------------------------------------------+
echo.

echo  [*] Installing llama-cpp-python...
"%PIP%" install llama-cpp-python --quiet
if %errorlevel% neq 0 (
    echo  [!!] Failed to install llama-cpp-python
) else (
    echo  [OK] llama-cpp-python installed
)

echo  [*] Installing pywin32...
"%PIP%" install pywin32 --quiet
if %errorlevel% neq 0 (
    echo  [!!] Failed to install pywin32
) else (
    echo  [OK] pywin32 installed
)

echo  [*] Installing psutil...
"%PIP%" install psutil --quiet
if %errorlevel% neq 0 (
    echo  [!!] Failed to install psutil
) else (
    echo  [OK] psutil installed
)

echo  [*] Installing pyspellchecker...
"%PIP%" install pyspellchecker --quiet
if %errorlevel% neq 0 (
    echo  [!!] Failed to install pyspellchecker
) else (
    echo  [OK] pyspellchecker installed
)

echo.
echo  +-----------------------------------------------------------+
echo  ^|  STEP 4 - CHECKING MODELS                                 ^|
echo  +-----------------------------------------------------------+
echo.

:: Check if any .gguf files already exist in models folder
set MODELS_FOUND=0
for %%f in ("%MODELS_DIR%\*.gguf") do set MODELS_FOUND=1

if "%MODELS_FOUND%"=="1" (
    echo  [OK] Models found in %MODELS_DIR%
    echo  [OK] Skipping model download step.
    goto SETUP_COMPLETE
)

echo  No models found. You need at least one to run NEURAL_GRID.
echo  Place .gguf files into: %MODELS_DIR%
echo.
echo  +-----------------------------------------------------------+
echo  ^|  TIER      MODEL                        SIZE   RAM        ^|
echo  +-----------------------------------------------------------+
echo  ^|  /fast     Qwen2.5-3B-Q4_K_M           ~2GB   4GB+       ^|
echo  ^|  /balanced Qwen3-8B-Q4_K_M             ~5GB   6GB+  REC  ^|
echo  ^|  /deep     Qwen2.5-14B-Q4_K_M          ~9GB   10GB+      ^|
echo  +-----------------------------------------------------------+
echo.
echo  DOWNLOAD LINKS:
echo.
echo  [1] Qwen2.5-3B  ^(Fast - good for older PCs^)
echo      https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
echo.
echo  [2] Qwen3-8B  ^(Balanced - recommended for most PCs^)
echo      https://huggingface.co/Qwen/Qwen3-8B-GGUF
echo.
echo  [3] Qwen2.5-14B  ^(Deep - needs a powerful PC^)
echo      https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF
echo.
echo  TIP: Download the Q4_K_M version for best quality vs size.
echo.

set /p OPEN_LINKS="  Open all model pages in browser now? (y/n): "
if /i "%OPEN_LINKS%"=="y" (
    echo.
    echo  [*] Opening model pages...
    start https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF
    timeout /t 1 /nobreak >nul
    start https://huggingface.co/Qwen/Qwen3-8B-GGUF
    timeout /t 1 /nobreak >nul
    start https://huggingface.co/Qwen/Qwen2.5-14B-Instruct-GGUF
    echo  [OK] Pages opened in browser
)

:SETUP_COMPLETE
echo.
echo  +-----------------------------------------------------------+
echo  ^|  SETUP COMPLETE                                           ^|
echo  +-----------------------------------------------------------+
echo.
echo  Next steps:
echo.

if "%MODELS_FOUND%"=="1" (
    echo    1. Double-click NEURAL_GRID\launch.bat to start
    echo    2. Type /help inside the app to see all commands
) else (
    echo    1. Download at least one model ^(Q4_K_M recommended^)
    echo       and place the .gguf file into:
    echo       %MODELS_DIR%
    echo.
    echo    2. Double-click NEURAL_GRID\launch.bat to start
    echo    3. Type /help inside the app to see all commands
)

echo.
echo  +-----------------------------------------------------------+
echo  ^|  Plug in. Boot up. Stay offline.                         ^|
echo  +-----------------------------------------------------------+
echo.
pause
