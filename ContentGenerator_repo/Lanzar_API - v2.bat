@echo off

cd /d C:\Users\David\Desktop\Programacion\ContentGenerator\ContentGenerator_repo\ContentGeneratorAPI

call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload

pause