@echo off
chcp 65001 > nul
title Dashboard Formación Caribe

echo ==========================================
echo   Dashboard Formación Caribe - Argos
echo ==========================================
echo.

:: Ir a la carpeta del script
cd /d "%~dp0"

:: Buscar Python (Anaconda, WinPython, o sistema)
set PYTHON=
for %%P in (
    "%USERPROFILE%\anaconda3\python.exe"
    "%USERPROFILE%\Anaconda3\python.exe"
    "%LOCALAPPDATA%\anaconda3\python.exe"
    "%PROGRAMDATA%\anaconda3\python.exe"
    "%USERPROFILE%\miniconda3\python.exe"
) do (
    if exist %%P (
        set PYTHON=%%~P
        goto :found_python
    )
)

:: Buscar python en PATH
where python >nul 2>&1
if %ERRORLEVEL% == 0 (
    set PYTHON=python
    goto :found_python
)

echo ERROR: No se encontro Python.
echo Descarga Anaconda desde: https://www.anaconda.com
echo.
pause
exit /b 1

:found_python
echo Python encontrado: %PYTHON%
echo.

:: Verificar si Streamlit está instalado
%PYTHON% -c "import streamlit" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Instalando dependencias (solo la primera vez)...
    %PYTHON% -m pip install streamlit plotly xlsxwriter openpyxl --quiet
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR al instalar dependencias.
        pause
        exit /b 1
    )
    echo Dependencias instaladas correctamente.
    echo.
)

:: Verificar si ya hay una instancia corriendo en el puerto 8501
netstat -an | find "8501" | find "LISTENING" >nul 2>&1
if %ERRORLEVEL% == 0 (
    echo El dashboard ya esta corriendo.
    start "" "http://localhost:8501"
    goto :end
)

:: Lanzar Streamlit
echo Iniciando Dashboard...
start /B %PYTHON% -m streamlit run app.py --server.headless true --browser.gatherUsageStats false --server.port 8501

:: Esperar que arranque (hasta 15 segundos)
echo Esperando que el servidor inicie
set /a count=0
:wait_loop
timeout /t 1 /nobreak >nul
set /a count+=1
echo|set /p=.
netstat -an | find "8501" | find "LISTENING" >nul 2>&1
if %ERRORLEVEL% == 0 goto :open_browser
if %count% lss 15 goto :wait_loop

:open_browser
echo.
echo Dashboard activo.
start "" "http://localhost:8501"

:end
echo.
echo Para cerrar: cierra esta ventana.
echo URL: http://localhost:8501
echo.
pause
