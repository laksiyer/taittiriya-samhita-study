@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py build.py
) else (
  python build.py
)
echo.
echo Site build finished.
start "" "%~dp0docs\index.html"
echo.
pause
