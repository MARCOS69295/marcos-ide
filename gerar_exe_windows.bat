@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Uso: gerar_exe_windows.bat caminho\programa.mar
    echo Exemplo: gerar_exe_windows.bat exemplos\ola_mundo.mar
    pause
    exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
    echo Python nao encontrado. Instale Python 3.10+ para gerar programas EXE.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if errorlevel 1 goto erro
)

call .venv\Scripts\activate.bat
python -m pip install -r requirements-build.txt
if errorlevel 1 goto erro

python marcosc.py build "%~1" --output-dir dist --keep-marc
if errorlevel 1 goto erro

echo.
echo Processo concluido. Consulte a pasta dist.
pause
exit /b 0

:erro
echo.
echo Falha ao gerar o executavel. Leia as mensagens acima.
pause
exit /b 1
