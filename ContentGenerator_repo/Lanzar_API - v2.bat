@echo off
cd /d C:\Users\David\Desktop\ContentGenerator_Project\ContentGeneratorAPI

call .venv\Scripts\activate

python -m uvicorn app.main:app --reload

pause