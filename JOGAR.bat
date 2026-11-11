@echo off
chcp 65001 >nul
title ELOS DO VAZIO
cls
echo ========================================================
echo               INICIANDO ELOS DO VAZIO...
echo ========================================================
echo.
python main.py
if errorlevel 1 (
    echo.
    echo ========================================================
    echo  [AVISO] Nao foi possivel iniciar o jogo diretamente.
    echo  Verifique se o Python esta instalado no seu computador.
    echo  Para instalar as dependencias necessarias, execute:
    echo           INSTALAR_DEPENDENCIAS.bat
    echo ========================================================
    echo.
    pause
)

