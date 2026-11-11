@echo off
chcp 65001 >nul
title INSTALADOR DE DEPENDÊNCIAS - ELOS DO VAZIO
cls
echo ========================================================
echo        INSTALANDO DEPENDÊNCIAS DE ELOS DO VAZIO
echo ========================================================
echo.
echo 1/2. Atualizando gerenciador pip...
python -m pip install --upgrade pip
echo.
echo 2/2. Instalando pygame-ce...
python -m pip install -r requirements.txt
echo.
echo ========================================================
echo    Instalacao concluida com sucesso!
echo    Agora basta clicar duas vezes em "JOGAR.bat"
echo ========================================================
echo.
pause

