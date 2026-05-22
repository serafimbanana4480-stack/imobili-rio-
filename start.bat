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
::    rapid       Launch rapid intelligent scan (foreground)
::    full        Launch full end-to-end pipeline once
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
if /i "%CMD%"=="rapid"     goto :rapid
if /i "%CMD%"=="full"      goto :full
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
echo    [4] Rapid scan inteligente (5 min)
echo    [5] Pipeline completo uma vez
echo    [6] Engine 24h autonomo (scraping + ETL + scoring)
echo    [7] Tudo (Engine + API + Dashboard)
echo.
echo    [8] Diagnostico do ambiente (doctor)
echo    [9] Correr testes (pytest)
echo    [10] Instalar / atualizar dependencias
echo.
echo    [0] Sair
echo  ============================================================
echo.
set /p "CHOICE=  Escolhe uma opcao [1-10, 0=sair]: "
if "%CHOICE%"=="1" goto :dashboard
if "%CHOICE%"=="2" goto :ui
if "%CHOICE%"=="3" goto :api
if "%CHOICE%"=="4" goto :rapid
if "%CHOICE%"=="5" goto :full
if "%CHOICE%"=="6" goto :engine
if "%CHOICE%"=="7" goto :all
if "%CHOICE%"=="8" goto :doctor_pause
if "%CHOICE%"=="9" goto :test_pause
if "%CHOICE%"=="10" goto :install_pause
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
echo    start.bat rapid         Rapid scan inteligente
echo    start.bat full          Pipeline completo uma vez
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

:: -- Step 1: Detect best Python for bootstrapping (PATH + known install dirs) --
set "BOOTSTRAP_PY="

:: Try py launcher with explicit version first
py -3.12 --version >nul 2>&1
if !errorlevel! == 0 ( set "BOOTSTRAP_PY=py -3.12" & goto :found_py )

:: Try plain py launcher
py --version >nul 2>&1
if !errorlevel! == 0 ( set "BOOTSTRAP_PY=py" & goto :found_py )

:: Try python in PATH
python --version >nul 2>&1
if !errorlevel! == 0 ( set "BOOTSTRAP_PY=python" & goto :found_py )

:: Try python3 in PATH
python3 --version >nul 2>&1
if !errorlevel! == 0 ( set "BOOTSTRAP_PY=python3" & goto :found_py )

:: Try common user install locations (winget / official installer)
for %%V in (312 311 310 313) do (
    if not defined BOOTSTRAP_PY (
        if exist "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" (
            "%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe" --version >nul 2>&1
            if !errorlevel! == 0 set "BOOTSTRAP_PY=%LOCALAPPDATA%\Programs\Python\Python%%V\python.exe"
        )
    )
)

:: Try system-wide install
for %%V in (312 311 310 313) do (
    if not defined BOOTSTRAP_PY (
        if exist "%ProgramFiles%\Python%%V\python.exe" (
            "%ProgramFiles%\Python%%V\python.exe" --version >nul 2>&1
            if !errorlevel! == 0 set "BOOTSTRAP_PY=%ProgramFiles%\Python%%V\python.exe"
        )
    )
)

if not defined BOOTSTRAP_PY (
    echo.
    echo  ERRO: Python nao encontrado em nenhum local conhecido.
    echo  Por favor, instala o Python 3.12 de https://python.org
    echo  Certifica-te de marcar "Add Python to PATH" durante a instalacao.
    echo.
    pause
    goto :menu
)

:found_py
echo  Python encontrado: %BOOTSTRAP_PY%

:: -- Step 2: Validate / repair existing venv --
if exist "%PROJECT_ROOT%\venv312" (
    "%PROJECT_ROOT%\venv312\Scripts\python.exe" --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo  Venv existente esta quebrado. Recriando...
        rd /s /q "%PROJECT_ROOT%\venv312" >nul 2>&1
    )
)

:: -- Step 3: Create venv if missing --
if not exist "%PROJECT_ROOT%\venv312" (
    echo  Criando venv312...
    %BOOTSTRAP_PY% -m venv "%PROJECT_ROOT%\venv312"
    if !errorlevel! neq 0 (
        echo  ERRO ao criar venv. Verifica se o Python esta correto.
        pause
        goto :menu
    )
)

:: -- Step 4: Install dependencies --
echo  A atualizar pip...
"%PROJECT_ROOT%\venv312\Scripts\python.exe" -m pip install --upgrade pip --quiet
echo  A instalar dependencias do projeto...
"%PROJECT_ROOT%\venv312\Scripts\python.exe" -m pip install -e "%PROJECT_ROOT%\realestate_engine[dev]"
if !errorlevel! neq 0 (
    echo.
    echo  ERRO ao instalar dependencias.
    pause
    goto :menu
)

:: -- Step 5: Create data directories --
echo  A criar diretorios de dados...
if not exist "%PROJECT_ROOT%\data\db"      mkdir "%PROJECT_ROOT%\data\db"
if not exist "%PROJECT_ROOT%\data\cache"   mkdir "%PROJECT_ROOT%\data\cache"
if not exist "%PROJECT_ROOT%\data\exports" mkdir "%PROJECT_ROOT%\data\exports"
if not exist "%PROJECT_ROOT%\data\backups" mkdir "%PROJECT_ROOT%\data\backups"
if not exist "%PROJECT_ROOT%\logs"         mkdir "%PROJECT_ROOT%\logs"

:: -- Step 6: Initialise database --
echo  A inicializar base de dados...
"%PROJECT_ROOT%\venv312\Scripts\python.exe" -c "from realestate_engine.database.models import init_db; init_db()" 2>nul

:: -- Step 7: Create .env from template if missing --
if not exist "%PROJECT_ROOT%\.env" (
    copy "%PROJECT_ROOT%\.env.example" "%PROJECT_ROOT%\.env" >nul 2>&1
    echo  Ficheiro .env criado a partir do template.
    echo  Edita-o com os teus valores antes de correr o engine.
)

echo.
echo  ===== Instalacao concluida com sucesso! =====
echo.
pause
goto :menu

:doctor
:doctor_pause
call :check_python || goto :menu
echo.
echo  ===== Diagnostico =====
"%PY_CMD%" --version
echo.
echo  [Browser]
"%PY_CMD%" -c "from realestate_engine.scraping.browser_resolver import find_browser; p=find_browser(); print('  Browser:', p or 'NAO ENCONTRADO (define REE_CHROME_PATH)')" 2>nul
echo.
echo  [Database]
"%PY_CMD%" -c "from realestate_engine.database.repository import DatabaseRepository; r=DatabaseRepository(); print('  clean_listings:', len(r.get_clean_listings(limit=5)))" 2>nul
echo.
echo  [Ollama]
"%PY_CMD%" -c "import httpx, sys; r=httpx.get('http://localhost:11434/api/tags', timeout=5); print('  Ollama:', 'OK' if r.status_code==200 else 'OFFLINE')" 2>nul
echo.
echo  [Telegram]
"%PY_CMD%" -c "import os, httpx, sys; t=os.getenv('TELEGRAM_BOT_TOKEN'); print('  Telegram:', 'CONFIGURADO' if t else 'NAO CONFIGURADO')" 2>nul
echo.
pause
goto :menu

:test
:test_pause
call :check_python || goto :menu
pushd "%PROJECT_ROOT%"
"%PY_CMD%" -m pytest tests/ -v
popd
echo.
pause
goto :menu

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

:rapid
call :check_python || goto :end
pushd "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%"
set "ENRICH_SKIP_HEAVY=1"
echo  A iniciar rapid scan inteligente (5 min)...
"%PY_CMD%" -c "import asyncio; from realestate_engine.scheduler.orchestrator import Orchestrator; asyncio.run(Orchestrator().run_rapid_pipeline())"
popd
goto :end

:full
call :check_python || goto :end
pushd "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%"
echo  A correr pipeline completo uma vez...
"%PY_CMD%" -c "import asyncio; from realestate_engine.scheduler.orchestrator import Orchestrator; asyncio.run(Orchestrator().run_full_pipeline())"
popd
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
