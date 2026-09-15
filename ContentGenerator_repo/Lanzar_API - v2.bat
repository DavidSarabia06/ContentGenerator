@echo off

cd /d "%~dp0ContentGeneratorAPI"

call .venv\Scripts\activate.bat

python -m pip install -r requirements.txt

python -m uvicorn app.main:app --reload

pause