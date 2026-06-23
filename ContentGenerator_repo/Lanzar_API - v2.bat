@echo off

cd /d C:\Users\David\Desktop\ContentGenerator\ContentGenerator_repo\ContentGeneratorAPI

call .venv\Scripts\activate.bat

python -m uvicorn app.main:app --reload

pause