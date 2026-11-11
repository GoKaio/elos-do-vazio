@echo off
chcp 65001 >nul
setlocal EnableExtensions

cd /d "%~dp0"
echo ============================================================================
echo   ELOS DO VAZIO - AUTOMACAO COMPLETA DE ASSETS, EXECUTAVEL E INSTALADOR
echo ============================================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH do sistema.
    pause
    exit /b 1
)

echo [1/4] Verificando dependencias (pyinstaller, pillow, pygame-ce)...
python -m pip install --upgrade pyinstaller pillow pygame-ce
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias de build.
    pause
    exit /b 1
)

if exist "%~dp0Legacy-Dungeon_V0.2_vacaroxa.zip" (
    if not exist "%~dp0assets\Legacy-Dungeon\Final\Assets\Background_1.png" (
        echo [INFO] Extraindo pacote Legacy-Dungeon_V0.2_vacaroxa.zip para assets\Legacy-Dungeon...
        powershell -NoProfile -Command "Expand-Archive -LiteralPath '%~dp0Legacy-Dungeon_V0.2_vacaroxa.zip' -DestinationPath '%~dp0assets\Legacy-Dungeon' -Force"
    )
)

echo.
echo [2/4] Compilando jogo principal (dist\Elos_do_Vazio\Elos_do_Vazio.exe)...
echo [3/4] Empacotando payload e compilando instalador gotico (dist_installer\Instalador_Elos_do_Vazio.exe)...
python "%~dp0build_instalador.py" --all
if errorlevel 1 (
    echo.
    echo [ERRO] O processo de build encontrou uma falha. Verifique os logs acima.
    pause
    exit /b 1
)

if not exist "%~dp0dist\Elos_do_Vazio\Elos_do_Vazio.exe" (
    echo [ERRO] Executavel principal nao encontrado em dist\Elos_do_Vazio\Elos_do_Vazio.exe.
    pause
    exit /b 1
)

if not exist "%~dp0dist_installer\Instalador_Elos_do_Vazio.exe" (
    echo [ERRO] Instalador nao encontrado em dist_installer\Instalador_Elos_do_Vazio.exe.
    pause
    exit /b 1
)

echo.
echo ============================================================================
echo   BUILD CONCLUIDO COM SUCESSO!
echo   Jogo portatil : "%~dp0dist\Elos_do_Vazio\Elos_do_Vazio.exe"
echo   Instalador    : "%~dp0dist_installer\Instalador_Elos_do_Vazio.exe"
echo ============================================================================
echo.

echo [4/4] Abrindo pasta do instalador gerado...
explorer.exe "%~dp0dist_installer"
endlocal
