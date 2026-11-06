@echo off
setlocal enabledelayedexpansion
title HEPESmenu.free - Setup

echo ============================================
echo   HEPESmenu.free - Setup and Launcher
echo ============================================
echo.

REM ---------------------------------------------------------------
REM 1) Find Python
REM ---------------------------------------------------------------
set "PYEXE="

where py >nul 2>&1
if %errorlevel%==0 (
    set "PYEXE=py"
    goto :found_python
)

where python >nul 2>&1
if %errorlevel%==0 (
    set "PYEXE=python"
    goto :found_python
)

echo Python was not found on this PC.
echo.
echo Please install Python 3.10 or newer from:
echo   https://www.python.org/downloads/
echo.
echo IMPORTANT: during install, check the box
echo   "Add python.exe to PATH"
echo.
echo After installing, run this file again.
pause
exit /b 1

:found_python
echo Found Python using: %PYEXE%
%PYEXE% --version
echo.

REM ---------------------------------------------------------------
REM 2) Check Python version (need 3.8+)
REM ---------------------------------------------------------------
%PYEXE% -c "import sys; sys.exit(0 if sys.version_info >= (3,8) else 1)"
if not %errorlevel%==0 (
    echo.
    echo Your Python version is too old. Please install Python 3.10+
    echo from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM ---------------------------------------------------------------
REM 3) Make sure pip is available
REM ---------------------------------------------------------------
%PYEXE% -m pip --version >nul 2>&1
if not %errorlevel%==0 (
    echo pip not found, trying to bootstrap it...
    %PYEXE% -m ensurepip --upgrade
)

REM ---------------------------------------------------------------
REM 4) Check / install required packages
REM     - tkinter ships with standard Python installs on Windows
REM     - Pillow is used for the game-logo icons (optional feature)
REM ---------------------------------------------------------------
echo Checking tkinter (built into Python on Windows)...
%PYEXE% -c "import tkinter" >nul 2>&1
if not %errorlevel%==0 (
    echo.
    echo tkinter is missing from this Python install.
    echo Reinstall Python from python.org and make sure
    echo "tcl/tk and IDLE" is selected during setup.
    pause
    exit /b 1
) else (
    echo   OK
)

echo Checking Pillow (for game logo icons)...
%PYEXE% -c "import PIL" >nul 2>&1
if not %errorlevel%==0 (
    echo   Not found, installing...
    %PYEXE% -m pip install --quiet --upgrade pillow
    if not %errorlevel%==0 (
        echo   Could not install Pillow automatically.
        echo   The app will still run, logos will show as
        echo   plain text monograms instead of icons.
    ) else (
        echo   Installed.
    )
) else (
    echo   OK
)

echo.
echo ============================================
echo   Setup complete - launching HEPESmenu.free
echo ============================================
echo.

REM ---------------------------------------------------------------
REM 5) Launch the app
REM ---------------------------------------------------------------
cd /d "%~dp0"
%PYEXE% HEPESmenu.py

if not %errorlevel%==0 (
    echo.
    echo The app closed with an error. See the message above.
    pause
)

endlocal
