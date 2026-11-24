@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python nao encontrado. Instale Python 3.10+ e marque "Add Python to PATH".
  pause
  exit /b 1
)
python -m venv .venv
if errorlevel 1 goto erro
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo.
echo Instalacao concluida. Execute iniciar_marcOS.bat para abrir a IDE.
pause
exit /b 0
:erro
echo Falha na instalacao. Leia a mensagem acima.
pause
exit /b 1
