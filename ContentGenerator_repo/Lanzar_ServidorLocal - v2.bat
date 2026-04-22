@echo off
REM Ruta al proyecto web
cd /d C:\Users\David\Desktop\ContentGenerator_Project\ContentGeneratorWeb

REM Inicia el servidor HTTP local con Python 3.13
start cmd /k py -3.13 -m http.server 5500

REM Espera unos segundos
timeout /t 2 >nul

REM Abre en navegador con parámetro anti-caché
set TIMESTAMP=%RANDOM%
start http://localhost:5500/login.html?nocache=%TIMESTAMP%
