@echo off
REM One-time setup: virtual environment + dependencies
python -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist models mkdir models
if not exist templates mkdir templates
if not exist datasets mkdir datasets
echo.
echo Done. Next steps:
echo   run.bat --pick       (calibrate)
echo   run.bat --preview    (check detection)
echo   run.bat              (start fishing)
pause
