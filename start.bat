@echo off
chcp 65001 >nul 2>&1
setlocal EnableDelayedExpansion

::==============================================================================
::  Real Estate Opportunity Engine - Unified Launcher
::  Usage:  start.bat [command]
::    install     One-time setup (venv, deps, DB)
::    dashboard   Launch dashboard + API in two windows
::    api         Launch API server only (port 8000)
::    ui          Launch Streamlit dashboard only (port 8501)
::    engine      Launch 24h autonomous pipeline (foreground)
::    all         Launch engine + dashboard + API
::    test        Run pytest suite
::    doctor      Diagnose environment (Python, browser, DB)
::    menu        Interactive menu (default when no args)
::    help        Show command reference
::==============================================================================

set "PROJECT_ROOT=%~dp0"
set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"
set "PY_CMD=%PROJECT_ROOT%\venv312\Scripts\python.exe"
set "CMD=%~1"
if "%CMD%"=="" set "CMD=menu"

if /i "%CMD%"=="menu"      goto :menu
if /i "%CMD%"=="help"      goto :help
if /i "%CMD%"=="install"   goto :install
if /i "%CMD%"=="doctor"    goto :doctor
if /i "%CMD%"=="test"      goto :test
if /i "%CMD%"=="api"       goto :api
if /i "%CMD%"=="ui"        goto :ui
if /i "%CMD%"=="dashboard" goto :dashboard
if /i "%CMD%"=="engine"    goto :engine
if /i "%CMD%"=="all"       goto :all

echo.
echo Comando desconhecido: %CMD%
echo.
goto :help

:menu
title Real Estate Opportunity Engine
cls
echo.
echo  ============================================================
echo    Real Estate Opportunity Engine - Grande Porto
echo  ============================================================
echo.
echo    [1] Dashboard + API (recomendado)
echo    [2] So Dashboard      (porta 8501)
echo    [3] So API            (porta 8000)
echo    [4] Engine 24h autonomo (scraping + ETL + scoring)
echo    [5] Tudo (Engine + API + Dashboard)
echo.
echo    [6] Diagnostico do ambiente (doctor)
echo    [7] Correr testes (pytest)
echo    [8] Instalar / atualizar dependencias
echo.
echo    [0] Sair
echo  ============================================================
echo.
set /p "CHOICE=  Escolhe uma opcao [1-8, 0=sair]: "
if "%CHOICE%"=="1" goto :dashboard
if "%CHOICE%"=="2" goto :ui
if "%CHOICE%"=="3" goto :api
if "%CHOICE%"=="4" goto :engine
if "%CHOICE%"=="5" goto :all
if "%CHOICE%"=="6" goto :doctor_pause
if "%CHOICE%"=="7" goto :test_pause
if "%CHOICE%"=="8" goto :install_pause
if "%CHOICE%"=="0" goto :end
echo.
echo  Opcao invalida. Tenta outra vez.
timeout /t 2 >nul
goto :menu

:help
echo  ============================================================
echo    Real Estate Opportunity Engine - Unified Launcher
echo  ============================================================
echo.
echo    start.bat               Menu interativo
echo    start.bat install       Setup inicial (venv, deps, DB)
echo    start.bat doctor        Diagnostico do ambiente
echo    start.bat dashboard     Dashboard + API
echo    start.bat api           So API     (http://localhost:8000)
echo    start.bat ui            So Dashboard (http://localhost:8501)
echo    start.bat engine        Pipeline 24h autonomo
echo    start.bat all           Engine + Dashboard + API
echo    start.bat test          Suite pytest
echo    start.bat help          Esta ajuda
echo.
echo    Override de browser (Nodriver):
echo      set REE_CHROME_PATH=C:\path\to\chrome.exe
echo  ============================================================
echo.
pause
goto :end

:check_python
if not exist "%PY_CMD%" (
    echo.
    echo  ERRO: Python venv nao encontrado em:
    echo  %PY_CMD%
    echo.
    echo  Corre:  start.bat install
    echo.
    pause
    exit /b 1
)
exit /b 0

:install
:install_pause
echo.
echo  ===== Instalacao =====
where py >nul 2>&1
if %errorlevel%==0 ( set "BOOTSTRAP_PY=py" ) else ( set "BOOTSTRAP_PY=python" )
%BOOTSTRAP_PY% --version >nul 2>&1 || (
    echo  ERRO: Python nao encontrado. Instala de https://python.org
    pause
    goto :end
)
for /f "tokens=2" %%v in ('%BOOTSTRAP_PY% --version') do (
    echo  Python %%v detectado.
    for /f "tokens=1,2 delims=." %%a in ("%%v") do (
        if %%a LSS 3 (
            echo  ERRO: Python %%v detectado. Requerido >=3.10.
            pause
            goto :end
        )
        if %%a==3 if %%b LSS 10 (
            echo  ERRO: Python %%v detectado. Requerido >=3.10.
            pause
            goto :end
        )
    )
)
if not exist "%PROJECT_ROOT%\.env" (
    if exist "%PROJECT_ROOT%\.env.example" (
        copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul
        echo  .env criado a partir de .env.example. Preencha os valores antes de correr.
    )
)
if not exist "%PROJECT_ROOT%\venv312" (
    echo  Criando venv312...
    %BOOTSTRAP_PY% -m venv "%PROJECT_ROOT%\venv312" || ( pause & goto :end )
)
echo  Instalando dependencias...
"%PY_CMD%" -m pip install --upgrade pip
"%PY_CMD%" -m pip install -e "%PROJECT_ROOT%\realestate_engine" || ( pause & goto :end )
echo  Inicializando base de dados...
"%PY_CMD%" -c "from realestate_engine.database.models import init_db; init_db()" 2>nul
mkdir "%PROJECT_ROOT%\data" "%PROJECT_ROOT%\data\db" "%PROJECT_ROOT%\data\cache" "%PROJECT_ROOT%\data\exports" "%PROJECT_ROOT%\data\backups" "%PROJECT_ROOT%\logs" 2>nul
echo.
echo  Instalacao completa.
echo.
pause
goto :end

:doctor
:doctor_pause
call :check_python || goto :end
echo.
echo  ===== Diagnostico =====
"%PY_CMD%" --version
"%PY_CMD%" -c "from realestate_engine.scraping.browser_resolver import find_browser; p=find_browser(); print('Browser:', p or 'NAO ENCONTRADO (define REE_CHROME_PATH)')"
"%PY_CMD%" -c "from realestate_engine.database.repository import DatabaseRepository; r=DatabaseRepository(); print('DB clean_listings:', len(r.get_clean_listings(limit=5)))"
echo.
pause
goto :end

:test
:test_pause
call :check_python || goto :end
pushd "%PROJECT_ROOT%"
"%PY_CMD%" -m pytest realestate_engine/tests/ -v
popd
echo.
pause
goto :end

:api
call :check_python || goto :end
pushd "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%"
set "PORT=8000"
netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel%==0 ( set "PORT=8001" & echo  Porta 8000 ocupada, a usar 8001 )
echo  A iniciar API em http://localhost:%PORT%
"%PY_CMD%" -m realestate_engine.api.main
popd
goto :end

:ui
call :check_python || goto :end
pushd "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%"
echo  A iniciar Dashboard em http://localhost:8501
"%PY_CMD%" -m streamlit run realestate_engine/dashboard/app.py --server.port=8501 --server.address=0.0.0.0
popd
goto :end

:dashboard
call :check_python || goto :end
echo.
echo  A lancar Dashboard + API em janelas separadas...
start "Real Estate API"       cmd /k "%~f0" api
timeout /t 2 /nobreak >nul
start "Real Estate Dashboard" cmd /k "%~f0" ui
echo.
echo  Dashboard: http://localhost:8501
echo  API:       http://localhost:8000  (ou 8001 se 8000 ocupada)
echo  Docs:      http://localhost:8000/docs
echo.
timeout /t 4 >nul
goto :end

:engine
call :check_python || goto :end
pushd "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%"
set "ENRICH_SKIP_HEAVY=1"
echo  A iniciar engine 24h. Ctrl+C para parar.
"%PY_CMD%" -m realestate_engine.main_engine
popd
goto :end

:all
call :check_python || goto :end
echo.
echo  A lancar Engine + Dashboard + API...
start "Real Estate Engine 24H" cmd /k "%~f0" engine
timeout /t 3 /nobreak >nul
start "Real Estate API"        cmd /k "%~f0" api
timeout /t 2 /nobreak >nul
start "Real Estate Dashboard"  cmd /k "%~f0" ui
echo  Tudo lancado.
timeout /t 3 >nul
goto :end

:end
endlocal
