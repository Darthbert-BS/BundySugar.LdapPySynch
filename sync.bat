@echo off
setlocal enabledelayedexpansion

REM Check for python3
where python3 >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python 3 found, running script with python3
    python3 main.py
    goto :eof
)

REM Check for python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    REM Check if it's Python 3.x
    for /f "tokens=1,2 delims=." %%a in ('python -c "import sys; print(sys.version)"') do (
        set PYTHON_MAJOR=%%a
        set PYTHON_MINOR=%%b
    )
    if !PYTHON_MAJOR! EQU 3 (
        echo Python 3.x found, running script with python
        python main.py
    ) else (
        echo Python 2.x found. This script requires Python 3.x.
        pause
    )
    goto :eof
)

REM If we get here, no suitable Python was found
echo No suitable Python installation found. Please install Python 3.x.
pause

:eof
endlocal