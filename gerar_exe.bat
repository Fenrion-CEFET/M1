@echo off
REM ============================================================
REM  Gera o programa M1_Visao.exe a partir do m1_visao.py
REM  Rode UMA vez, neste PC (que tem Python). O .exe gerado
REM  funciona em qualquer PC com Windows, sem Python instalado.
REM ============================================================
cd /d "%~dp0"
set PY="C:\Users\alencar\AppData\Local\Programs\Python\Python312\python.exe"

echo [1/3] Instalando o PyInstaller e as bibliotecas...
%PY% -m pip install --upgrade pyinstaller opencv-contrib-python numpy requests
if errorlevel 1 goto erro

echo.
echo [2/3] Gerando o executavel (demora 1 a 3 minutos)...
%PY% -m PyInstaller --noconfirm --clean --onefile --console --name M1_Visao m1_visao.py
if errorlevel 1 goto erro

echo.
echo [3/3] Copiando o executavel para esta pasta...
copy /Y dist\M1_Visao.exe . >nul
echo.
echo PRONTO! O arquivo M1_Visao.exe esta nesta pasta.
echo Pode copiar so ele para outros computadores.
pause
exit /b 0

:erro
echo.
echo Algo deu errado. Copie as mensagens acima e envie.
pause
exit /b 1
