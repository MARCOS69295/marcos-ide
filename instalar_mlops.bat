@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Ambiente virtual nao encontrado. Execute instalar_windows.bat primeiro.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python -m pip install -r requirements-ml.txt
if errorlevel 1 (
  echo Falha ao instalar dependencias de Machine Learning.
  pause
  exit /b 1
)
echo Dependencias de ML/MLOps instaladas.
echo PyTorch e opcional. Para CPU, execute instalar_pytorch_cpu.bat. Para CUDA, consulte pytorch.org.
pause
