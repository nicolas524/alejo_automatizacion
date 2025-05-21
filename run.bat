@echo off
chcp 65001 >nul
title ⚡⚙  Hacker-Style Launcher ⚙⚡
color 0A
mode con: cols=80 lines=25
cls

:: ───────────────────────────────────────────────────────────────────────────
echo.
echo             ██╗  ██╗ ██████╗ ██████╗ ██████╗ ██╗   ██╗
echo             ██║ ██╔╝██╔═══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝
echo             █████╔╝ ██║   ██║██║  ██║██║  ██║ ╚████╔╝ 
echo             ██╔═██╗ ██║   ██║██║  ██║██║  ██║  ╚██╔╝  
echo             ██║  ██╗╚██████╔╝██████╔╝██████╔╝   ██║   
echo             ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═════╝    ╚═╝                
echo.
echo          Más que Tecnología, Resultados que Transforman
echo ───────────────────────────────────────────────────────────────────────────
echo.
echo    Iniciando secuencia de arranque...
timeout /t 5 >nul

echo.
echo    Cargando módulos principales:
set /a total=40
set /a step=100/total
set "bar="
for /L %%i in (1,1,%total%) do (
    <nul set /p="▓"
    ping -n 1 127.0.0.1 >nul
)
echo.
echo    [*] Módulos cargados: 100%%
echo.
timeout /t 1 >nul

echo    Estableciendo entorno Python...
timeout /t 1 >nul

rem 1) Activar entorno virtual "venv"
echo    [*] Activando venv...
call "%~dp0venv\Scripts\activate.bat" 2>nul
if ERRORLEVEL 1 (
    echo    [ERROR] No pude activar el entorno virtual.
    pause
    exit /b 1
)
echo    [OK] venv activo.
echo.

rem 2) Ejecutar core.py
echo    [*] Ejecutando core.py...
python "%~dp0python\core.py"
if ERRORLEVEL 1 (
    echo    [ERROR] core.py falló.
    pause
    exit /b 1
)
echo    [OK] core.py completado.
echo.

rem 3) Ejecutar docs_maker.py
echo    [*] Ejecutando docs_maker.py...
python "%~dp0python\docs_maker.py"
if ERRORLEVEL 1 (
    echo    [ERROR] docs_maker.py falló.
    pause
    exit /b 1
)
echo    [OK] docs_maker.py completado.
echo.

echo ───────────────────────────────────────────────────────────────────────────
echo    🚀 Todo terminado con éxito. Resultados disponibles en:
echo       📂 la carpeta outputs
echo ───────────────────────────────────────────────────────────────────────────
pause
exit /b 0