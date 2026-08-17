@echo off
rem Launches the desktop GUI by double-click. Always runs from this file's
rem own folder (not wherever it happened to be launched from), and pauses on
rem a crash so the window doesn't just flash and vanish before you can read
rem the error - the same fix the Installation Manual suggests doing by hand
rem via a terminal, just without needing to open one.
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
    py valves_gui.py
) else (
    python valves_gui.py
)

if errorlevel 1 (
    echo.
    echo valves_gui.py exited with an error - see above.
    pause
)
