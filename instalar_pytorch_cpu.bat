@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Execute instalar_windows.bat primeiro.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
  echo Falha ao instalar PyTorch CPU. Consulte https://pytorch.org/get-started/locally/ para escolher a versao adequada.
  pause
  exit /b 1
)
echo PyTorch CPU instalado.
pause
