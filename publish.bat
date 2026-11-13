@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py build.py
) else (
  python build.py
)
git add .
set /p msg=Commit message (press Enter for "Update TS study"): 
if "%msg%"=="" set msg=Update TS study
git commit -m "%msg%"
git push
echo.
pause
