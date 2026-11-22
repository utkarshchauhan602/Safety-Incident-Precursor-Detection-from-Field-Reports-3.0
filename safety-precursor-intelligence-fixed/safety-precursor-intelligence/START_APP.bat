@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Safety Precursor Intelligence - Launcher
set "LOG=%~dp0startup_log.txt"
echo Safety Precursor Intelligence startup > "%LOG%"
echo Folder: %CD% >> "%LOG%"
echo. 
echo ==========================================
echo   SAFETY PRECURSOR INTELLIGENCE
echo ==========================================
echo.
echo This window will stay open so you can see errors.
echo Startup log: startup_log.txt
echo.

if not exist "%~dp0app.py" (
  echo ERROR: app.py is missing from this folder.
  echo Extract the COMPLETE ZIP first, then run START_APP.bat.
  echo Missing app.py >> "%LOG%"
  pause
  exit /b 1
)

set "PYEXE="
set "PYARGS="

where py >nul 2>nul
if not errorlevel 1 (
  py -3.13 --version >nul 2>nul
  if not errorlevel 1 (
    set "PYEXE=py"
    set "PYARGS=-3.13"
  )
  if not defined PYEXE (
    py -3.12 --version >nul 2>nul
    if not errorlevel 1 (
      set "PYEXE=py"
      set "PYARGS=-3.12"
    )
  )
)

if not defined PYEXE (
  where python >nul 2>nul
  if not errorlevel 1 (
    for /f "tokens=2" %%V in ('python -c "import sys; print(str(sys.version_info.major)+'.'+str(sys.version_info.minor))" 2^>nul') do set "PYVER=%%V"
    if "%PYVER%"=="3.12" (
      set "PYEXE=python"
    )
    if "%PYVER%"=="3.13" (
      set "PYEXE=python"
    )
  )
)

if not defined PYEXE (
  echo ERROR: Python 3.12 or 3.13 was not found.
  echo.
  echo Your earlier screenshot showed Python 3.15.
  echo This project uses scikit-learn; use Python 3.12 or 3.13 for
  echo the most reliable compatibility.
  echo.
  echo Install Python 3.13 from https://www.python.org/downloads/
  echo During installation, enable "Add python.exe to PATH".
  echo Then close this window, delete the .venv folder if one exists,
  echo and double-click START_APP.bat again.
  echo Python 3.12/3.13 not found. >> "%LOG%"
  pause
  exit /b 1
)

echo Using Python:
%PYEXE% %PYARGS% --version
%PYEXE% %PYARGS% --version >> "%LOG%" 2>&1

if not exist "%~dp0.venv\Scripts\python.exe" (
  echo.
  echo Creating project environment...
  %PYEXE% %PYARGS% -m venv "%~dp0.venv" >> "%LOG%" 2>&1
  if errorlevel 1 (
    echo ERROR: Could not create virtual environment. See startup_log.txt.
    pause
    exit /b 1
  )
)

echo.
echo Installing/checking libraries. This may take a few minutes...
"%~dp0.venv\Scripts\python.exe" -m pip install --upgrade pip >> "%LOG%" 2>&1
if errorlevel 1 goto install_failed
"%~dp0.venv\Scripts\python.exe" -m pip install -r "%~dp0requirements.txt" >> "%LOG%" 2>&1
if errorlevel 1 goto install_failed

echo.
echo Launching the app...
echo Launch command started >> "%LOG%"
"%~dp0.venv\Scripts\python.exe" -m streamlit run "%~dp0app.py"
if errorlevel 1 (
  echo.
  echo ERROR: Streamlit stopped. Details are in startup_log.txt.
  echo Streamlit exited with an error >> "%LOG%"
  pause
  exit /b 1
)
goto end

:install_failed
echo.
echo ERROR: Package installation failed.
echo Open startup_log.txt and send it to ChatGPT.
echo Package installation failed >> "%LOG%"
pause
exit /b 1

:end
endlocal
