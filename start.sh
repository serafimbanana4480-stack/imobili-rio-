#!/usr/bin/env bash
# ============================================================================
#  Real Estate Opportunity Engine — Unified Launcher (macOS / Linux)
#  Mirror of start.bat. Kept in sync via tests/test_production_readiness_onda2.py.
#
#  Usage:  ./start.sh [command]
#    install     One-time setup (venv, deps, DB)
#    dashboard   Launch dashboard + API in two terminals (best effort)
#    api         Launch API server only (port 8000)
#    ui          Launch Streamlit dashboard only (port 8501)
#    rapid       Launch rapid intelligent scan (foreground)
#    full        Launch full end-to-end pipeline once
#    engine      Launch 24h autonomous pipeline (foreground)
#    all         Launch engine + dashboard + API
#    test        Run pytest suite
#    doctor      Diagnose environment (Python, browser, DB)
#    menu        Interactive menu (default when no args)
#    help        Show command reference
# ============================================================================
set -euo pipefail

# Resolve script directory even when invoked via symlink.
SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
PROJECT_ROOT="$(cd -P "$(dirname "$SOURCE")" && pwd)"

# venv layout matches start.bat (venv312/) so Windows & Unix share artefacts
# when checked out under e.g. WSL.
VENV_DIR="$PROJECT_ROOT/venv312"
IS_WSL=0
case "$(uname -s)" in
  Linux)
    if [[ -n "${WSL_DISTRO_NAME:-}" ]] || grep -qi microsoft /proc/version 2>/dev/null; then
      IS_WSL=1
    fi
    ;;
esac

resolve_python() {
  if [[ -x "$VENV_DIR/bin/python" ]]; then
    PY_CMD="$VENV_DIR/bin/python"
  elif [[ "$IS_WSL" -eq 1 ]] && [[ -x "$VENV_DIR/Scripts/python.exe" ]]; then
    PY_CMD="$VENV_DIR/Scripts/python.exe"   # WSL pointing at a Windows venv
  else
    PY_CMD=""
  fi
}

resolve_python

CMD="${1:-menu}"

# ── Helpers ────────────────────────────────────────────────────────────────
check_python() {
  if [[ -z "$PY_CMD" ]] || [[ ! -x "$PY_CMD" ]]; then
    echo
    echo " ERRO: Python venv não encontrado ou incompatível em:"
    echo " $VENV_DIR"
    echo
    echo " Corre:  ./start.sh install"
    echo "        (recria o venv Unix em $VENV_DIR/bin/python)"
    echo
    exit 1
  fi
}

cmd_rapid() {
  check_python
  cd "$PROJECT_ROOT"
  export PYTHONPATH="$PROJECT_ROOT"
  export ENRICH_SKIP_HEAVY=1
  echo " A iniciar rapid scan inteligente (5 min)..."
  "$PY_CMD" -c "import asyncio; from realestate_engine.scheduler.orchestrator import Orchestrator; asyncio.run(Orchestrator().run_rapid_pipeline())"
}

cmd_full() {
  check_python
  cd "$PROJECT_ROOT"
  export PYTHONPATH="$PROJECT_ROOT"
  echo " A correr pipeline completo uma vez..."
  "$PY_CMD" -c "import asyncio; from realestate_engine.scheduler.orchestrator import Orchestrator; asyncio.run(Orchestrator().run_full_pipeline())"
}

# Detect a terminal launcher to spawn extra windows for `dashboard` / `all`.
# Falls back to running the second command in the background so the script
# remains useful in headless / CI environments.
spawn_in_terminal() {
  local title="$1"; shift
  local cmd="$*"
  if command -v osascript >/dev/null 2>&1; then
    # macOS Terminal.app
    osascript -e "tell app \"Terminal\" to do script \"cd '$PROJECT_ROOT' && $cmd\"" >/dev/null
  elif command -v gnome-terminal >/dev/null 2>&1; then
    gnome-terminal --title="$title" -- bash -lc "cd '$PROJECT_ROOT' && $cmd; exec bash"
  elif command -v x-terminal-emulator >/dev/null 2>&1; then
    x-terminal-emulator -T "$title" -e bash -lc "cd '$PROJECT_ROOT' && $cmd; exec bash"
  else
    echo " (sem terminal GUI detectado — a correr em background: $title)"
    ( cd "$PROJECT_ROOT" && eval "$cmd" ) &
  fi
}

# ── Commands ───────────────────────────────────────────────────────────────
cmd_help() {
  cat <<EOF
 ============================================================
   Real Estate Opportunity Engine — Unified Launcher
 ============================================================

   ./start.sh                Menu interactivo
   ./start.sh install        Setup inicial (venv, deps, DB)
   ./start.sh doctor         Diagnóstico do ambiente
   ./start.sh dashboard      Dashboard + API
   ./start.sh api            Só API     (http://localhost:8000)
   ./start.sh ui             Só Dashboard (http://localhost:8501)
   ./start.sh rapid          Rapid scan inteligente
   ./start.sh full           Pipeline completo uma vez
   ./start.sh engine         Pipeline 24h autónomo
   ./start.sh all            Engine + Dashboard + API
   ./start.sh test           Suite pytest
   ./start.sh help           Esta ajuda

   Override de browser (Nodriver):
     export REE_CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
 ============================================================
EOF
}

cmd_menu() {
  cat <<EOF

 ============================================================
   Real Estate Opportunity Engine — Grande Porto
 ============================================================

   [1] Dashboard + API (recomendado)
   [2] Só Dashboard      (porta 8501)
   [3] Só API            (porta 8000)
   [4] Rapid scan inteligente (5 min)
   [5] Pipeline completo uma vez
   [6] Engine 24h autónomo (scraping + ETL + scoring)
   [7] Tudo (Engine + API + Dashboard)

   [8] Diagnóstico do ambiente (doctor)
   [9] Correr testes (pytest)
   [10] Instalar / atualizar dependências

   [0] Sair
 ============================================================
EOF
  read -r -p "  Escolhe uma opção [1-10, 0=sair]: " choice
  case "$choice" in
    1) cmd_dashboard ;;
    2) cmd_ui ;;
    3) cmd_api ;;
    4) cmd_rapid ;;
    5) cmd_full ;;
    6) cmd_engine ;;
    7) cmd_all ;;
    8) cmd_doctor ;;
    9) cmd_test ;;
    10) cmd_install ;;
    0) exit 0 ;;
    *) echo "  Opção inválida."; sleep 1; cmd_menu ;;
  esac
}

cmd_install() {
  echo
  echo " ===== Instalação ====="

  # Detect the best Python command to use for bootstrapping
  BOOTSTRAP_PY=""
  for cmd in python3.12 python3 python; do
    if command -v "$cmd" >/dev/null 2>&1; then
      BOOTSTRAP_PY="$cmd"
      break
    fi
  done

  if [[ -z "$BOOTSTRAP_PY" ]]; then
    echo " ERRO: Python não encontrado. Instala via brew/apt/dnf."
    exit 1
  fi

  # Validate existing venv
  if [[ -d "$VENV_DIR" ]]; then
    # Try to use the python in the venv
    if ! "$VENV_DIR/bin/python" --version >/dev/null 2>&1; then
      echo " Venv existente parece estar quebrado. Recriando..."
      rm -rf "$VENV_DIR"
    fi
  fi

  if [[ ! -d "$VENV_DIR" ]]; then
    echo " A criar venv312 usando $BOOTSTRAP_PY..."
    "$BOOTSTRAP_PY" -m venv "$VENV_DIR"
  fi

  PY_CMD="$VENV_DIR/bin/python"
  echo " A instalar dependências..."
  "$PY_CMD" -m pip install --upgrade pip
  "$PY_CMD" -m pip install -e "$PROJECT_ROOT/realestate_engine[dev]"
  echo " A inicializar base de dados..."
  "$PY_CMD" -c "from realestate_engine.database.models import init_db; init_db()" 2>/dev/null || true
  mkdir -p "$PROJECT_ROOT"/data/{db,cache,exports,backups} "$PROJECT_ROOT/logs"
  echo
  echo " Instalação completa."
}

cmd_doctor() {
  check_python
  echo
  echo " ===== Diagnóstico ====="
  "$PY_CMD" --version
  "$PY_CMD" -c "from realestate_engine.scraping.browser_resolver import find_browser; p=find_browser(); print('Browser:', p or 'NAO ENCONTRADO (define REE_CHROME_PATH)')"
  "$PY_CMD" -c "from realestate_engine.database.repository import DatabaseRepository; r=DatabaseRepository(); print('DB clean_listings:', len(r.get_clean_listings(limit=5)))"
}

cmd_test() {
  check_python
  cd "$PROJECT_ROOT"
  "$PY_CMD" -m pytest tests/ -v
}

cmd_api() {
  check_python
  cd "$PROJECT_ROOT"
  export PYTHONPATH="$PROJECT_ROOT"
  local PORT=8000
  if command -v lsof >/dev/null 2>&1 && lsof -nPiTCP:8000 -sTCP:LISTEN >/dev/null 2>&1; then
    PORT=8001
    echo " Porta 8000 ocupada, a usar 8001"
  fi
  echo " A iniciar API em http://localhost:$PORT"
  PORT=$PORT "$PY_CMD" -m realestate_engine.api.main
}

cmd_ui() {
  check_python
  cd "$PROJECT_ROOT"
  export PYTHONPATH="$PROJECT_ROOT"
  echo " A iniciar Dashboard em http://localhost:8501"
  "$PY_CMD" -m streamlit run realestate_engine/dashboard/app.py \
    --server.port=8501 --server.address=0.0.0.0
}

cmd_dashboard() {
  check_python
  echo
  echo " A lançar Dashboard + API..."
  spawn_in_terminal "Real Estate API" "./start.sh api"
  sleep 2
  spawn_in_terminal "Real Estate Dashboard" "./start.sh ui"
  echo
  echo " Dashboard: http://localhost:8501"
  echo " API:       http://localhost:8000  (ou 8001 se 8000 ocupada)"
  echo " Docs:      http://localhost:8000/docs"
}

cmd_engine() {
  check_python
  cd "$PROJECT_ROOT"
  export PYTHONPATH="$PROJECT_ROOT"
  export ENRICH_SKIP_HEAVY="${ENRICH_SKIP_HEAVY:-1}"
  echo " A iniciar engine 24h. Ctrl+C para parar."
  "$PY_CMD" -m realestate_engine.main_engine
}

cmd_all() {
  check_python
  echo
  echo " A lançar Engine + Dashboard + API..."
  spawn_in_terminal "Real Estate Engine 24H" "./start.sh engine"
  sleep 3
  spawn_in_terminal "Real Estate API" "./start.sh api"
  sleep 2
  spawn_in_terminal "Real Estate Dashboard" "./start.sh ui"
  echo " Tudo lançado."
}

# ── Dispatch ───────────────────────────────────────────────────────────────
case "$CMD" in
  menu)      cmd_menu ;;
  help|-h|--help) cmd_help ;;
  install)   cmd_install ;;
  doctor)    cmd_doctor ;;
  test)      cmd_test ;;
  api)       cmd_api ;;
  ui)        cmd_ui ;;
  dashboard) cmd_dashboard ;;
  rapid)     cmd_rapid ;;
  full)      cmd_full ;;
  engine)    cmd_engine ;;
  all)       cmd_all ;;
  *)
    echo
    echo "Comando desconhecido: $CMD"
    echo
    cmd_help
    exit 1
    ;;
esac
