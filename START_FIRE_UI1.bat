@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 fire_ui1_launch.py %*
) else (
  python fire_ui1_launch.py %*
)
endlocal
