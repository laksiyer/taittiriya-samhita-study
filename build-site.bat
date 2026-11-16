@echo off
cd /d "%~dp0"

python -c "import aksharamukha" >nul 2>&1
if errorlevel 1 (
    echo.
    echo First-time transliteration setup...
    echo Installing Aksharamukha for Devanagari, IAST, ITRANS, Grantha, Telugu, Kannada, and Malayalam.
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo Aksharamukha could not be installed.
        echo Check your internet connection, then double-click build-site.bat again.
        pause
        exit /b 1
    )
)

python build.py
if errorlevel 1 (
    echo.
    echo The site could not be built.
    pause
    exit /b 1
)

start "" "docs\index.html"
