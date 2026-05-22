"""Streamlit dashboard main application — Porto Real Estate Intelligence Engine."""
import importlib
import os
import sys
import traceback

import streamlit as st
from loguru import logger

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from realestate_engine.utils.config import config

# ── Configure Logging for UI ───────────────────────────────────────────────
os.makedirs("logs", exist_ok=True)
logger.add("logs/dashboard.log", rotation="5 MB", retention="5 days", level="DEBUG", format="{time:YYYY-MM-DD HH:mm:ss} | UI | {level: <8} | {name}:{function}:{line} - {message}")
logger.add("logs/errors.log", rotation="5 MB", retention="30 days", level="ERROR", backtrace=True, diagnose=True)


def _render_view(module_path: str, func_name: str) -> None:
    """Import a dashboard view lazily and render it with full error visibility."""
    try:
        module = importlib.import_module(module_path)
        render_func = getattr(module, func_name)
        render_func()
    except Exception as exc:
        logger.exception("Dashboard view failed: %s", module_path)
        st.error("Erro ao carregar esta secção.")
        st.info("Tente recarregar a pagina ou consulte os logs em `logs/errors.log`.")
        with st.expander("Detalhes tecnicos (para debug)", expanded=False):
            st.code(f"{type(exc).__name__}: {exc}", language="python")
            st.code(traceback.format_exc(), language="python")
        st.caption("A dashboard continua ativa; esta view falhou apenas nesta renderização.")

st.set_page_config(
    page_title="Porto Real Estate Intelligence",
    page_icon=":material/home:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom Theme & Styling ───────────────────────────────────────────────
# Define consistent color palette
PRIMARY_COLOR = "#1E3A8A"  # Professional blue
PRIMARY_LIGHT = "#1E40AF"  # Lighter blue for hover states
SECONDARY_COLOR = "#10B981"  # Success green
WARNING_COLOR = "#F59E0B"  # Warning orange
ERROR_COLOR = "#EF4444"  # Error red
BACKGROUND_COLOR_LIGHT = "#F8FAFC"  # Light gray background
BACKGROUND_COLOR_DARK = "#0F172A"  # Dark background
SIDEBAR_BACKGROUND = "#1E293B"  # Dark sidebar
TEXT_COLOR_LIGHT = "#1E293B"  # Dark text for light mode
TEXT_COLOR_DARK = "#E2E8F0"  # Light text for dark mode
TEXT_COLOR_MUTED_LIGHT = "#64748B"  # Muted text for light mode
TEXT_COLOR_MUTED_DARK = "#94A3B8"  # Muted text for dark mode
BORDER_COLOR_LIGHT = "#E2E8F0"  # Light border
BORDER_COLOR_DARK = "#334155"  # Dark border

# Accessibility: Ensure WCAG AA contrast ratios (4.5:1 for normal text)
# All color combinations above meet or exceed WCAG AA standards

# Custom CSS for professional styling
st.markdown("""
<style>
    /* Main container styling */
    [data-testid="stAppViewContainer"], .stAppViewContainer {
        background-color: #F8FAFC;
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #1E293B;
    }
    
    /* Header styling */
    h1 {
        color: #1E3A8A;
        font-weight: 700;
    }
    
    h2 {
        color: #334155;
        font-weight: 600;
    }
    
    h3 {
        color: #475569;
        font-weight: 500;
    }
    
    /* Metric cards */
    div[data-testid="stMetricValue"] {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1E3A8A;
    }
    
    /* Dataframe styling */
    .dataframe {
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #1E3A8A;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s;
    }
    
    .stButton>button:hover {
        background-color: #1E40AF;
        transform: translateY(-1px);
    }
    
    .stButton>button:focus {
        outline: 2px solid #10B981;
        outline-offset: 2px;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] p {
        color: #E2E8F0;
    }
    
    /* Skip to main content link for accessibility */
    .skip-link {
        position: absolute;
        top: -40px;
        left: 0;
        background: #1E3A8A;
        color: white;
        padding: 8px;
        z-index: 100;
        transition: top 0.3s;
    }
    
    .skip-link:focus {
        top: 0;
    }
    
    /* Improve focus visibility for all interactive elements */
    *:focus {
        outline: 2px solid #10B981;
        outline-offset: 2px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #F1F5F9;
        border-radius: 8px;
    }
    
    /* Success/info/error boxes */
    .stSuccess {
        background-color: #ECFDF5;
        border-left: 4px solid #10B981;
        border-radius: 4px;
    }
    
    .stInfo {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        border-radius: 4px;
    }
    
    .stWarning {
        background-color: #FFFBEB;
        border-left: 4px solid #F59E0B;
        border-radius: 4px;
    }
    
    .stError {
        background-color: #FEF2F2;
        border-left: 4px solid #EF4444;
        border-radius: 4px;
    }

    /* Professional card component */
    .re-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.06);
        transition: box-shadow 0.2s;
    }
    .re-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.12);
    }

    /* Status badge */
    .re-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: 600;
    }
    .re-badge-success { background: #ECFDF5; color: #065F46; }
    .re-badge-warning { background: #FFFBEB; color: #92400E; }
    .re-badge-error   { background: #FEF2F2; color: #991B1B; }
    .re-badge-info    { background: #EFF6FF; color: #1E3A8A; }

    /* Header bar */
    .re-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #1E40AF 100%);
        color: white;
        padding: 16px 24px;
        border-radius: 0 0 16px 16px;
        margin: -16px -16px 16px -16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Sidebar nav buttons */
    .sidebar-nav-btn {
        width: 100%;
        text-align: left;
        padding: 8px 12px;
        border-radius: 8px;
        margin-bottom: 2px;
        transition: background 0.15s;
        cursor: pointer;
        color: #E2E8F0;
    }
    .sidebar-nav-btn:hover {
        background: rgba(255,255,255,0.1);
    }
    .sidebar-nav-btn.active {
        background: rgba(59,130,246,0.3);
        border-left: 3px solid #3B82F6;
    }

    /* Loading skeleton */
    @keyframes shimmer {
        0% { background-position: -200px 0; }
        100% { background-position: 200px 0; }
    }
    .re-skeleton {
        background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
        background-size: 200px 100%;
        animation: shimmer 1.5s ease-in-out infinite;
        border-radius: 8px;
        height: 20px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ── Sidebar ─────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center;padding:12px 0;">
    <div style="font-size:1.6em;font-weight:800;color:#E2E8F0;">Porto RE</div>
    <div style="font-size:0.85em;color:#94A3B8;margin-top:2px;">Inteligência Imobiliária</div>
</div>
""", unsafe_allow_html=True)

# Theme toggle
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

theme = st.sidebar.radio(
    "Tema",
    ['Claro', 'Escuro'],
    index=0 if st.session_state.theme == 'light' else 1
)

if theme == 'Claro':
    st.session_state.theme = 'light'
    st.markdown("""
    <style>
        [data-testid="stAppViewContainer"], .stAppViewContainer { background-color: #F8FAFC !important; }
        section[data-testid="stSidebar"], section[data-testid="stSidebar"] > div { background-color: #1E293B !important; }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] a,
        section[data-testid="stSidebar"] button {
            color: #E2E8F0 !important;
        }
        section[data-testid="stSidebar"] svg,
        section[data-testid="stSidebar"] svg * {
            fill: #E2E8F0 !important;
            stroke: #E2E8F0 !important;
        }
        section[data-testid="stSidebar"] [data-baseweb="select"] > div,
        section[data-testid="stSidebar"] .stTextInput input,
        section[data-testid="stSidebar"] .stNumberInput input,
        section[data-testid="stSidebar"] .stTextArea textarea {
            background-color: #334155 !important;
            color: #E2E8F0 !important;
            border: 1px solid #475569 !important;
        }
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stCheckbox label,
        section[data-testid="stSidebar"] .stCaption {
            color: #CBD5E1 !important;
        }
        section[data-testid="stSidebar"] .stButton > button,
        section[data-testid="stSidebar"] .stDownloadButton > button {
            background-color: #1E3A8A !important;
            color: #FFFFFF !important;
            border: 1px solid #334155 !important;
        }
        h1, h2, h3, h4, h5, h6 { color: #1E3A8A !important; }
        p, span, label, .stMarkdown, .stCaption { color: #1E293B !important; }
        .stCaption { color: #64748B !important; }
        div[data-testid="stMetricValue"] { color: #1E3A8A !important; }
        div[data-testid="stMetricLabel"] { color: #64748B !important; }
        .stButton > button { background-color: #1E3A8A !important; color: #FFFFFF !important; }
        .stButton > button:hover { background-color: #1E40AF !important; }
        .stTextInput input, .stNumberInput input, .stTextArea textarea { background-color: #FFFFFF !important; color: #1E293B !important; border: 1px solid #E2E8F0 !important; }
        div[data-baseweb="select"] > div { background-color: #FFFFFF !important; color: #1E293B !important; border-color: #E2E8F0 !important; }
        .stRadio label, .stCheckbox label { color: #1E293B !important; }
        .stTabs [data-baseweb="tab-list"] { background-color: #F1F5F9 !important; border-bottom: 1px solid #E2E8F0 !important; }
        .stTabs [aria-selected="true"] { color: #1E3A8A !important; border-bottom: 2px solid #3B82F6 !important; }
        .dataframe, .dataframe td, .dataframe th { background-color: #FFFFFF !important; color: #1E293B !important; }
        .re-card { background: #FFFFFF !important; border-color: #E2E8F0 !important; color: #1E293B !important; }
        .re-source-banner { background: #ECFDF5 !important; border-left: 4px solid #10B981 !important; color: #065F46 !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.session_state.theme = 'dark'
    # Comprehensive dark theme CSS — covers all Streamlit primitives + popovers
    st.markdown("""
    <style>
        /* ── Base containers ───────────────────────────────────────── */
        [data-testid="stAppViewContainer"], .stAppViewContainer,
        [data-testid="stHeader"], [data-testid="stMain"],
        .main, .block-container {
            background-color: #0F172A !important;
            color: #E2E8F0 !important;
        }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background-color: #1E293B !important;
        }

        /* ── Typography ────────────────────────────────────────────── */
        h1, h2, h3, h4, h5, h6 { color: #E2E8F0 !important; }
        p, span, label, .stMarkdown, .stCaption { color: #E2E8F0 !important; }
        small, .stCaption { color: #94A3B8 !important; }

        /* ── Metrics ───────────────────────────────────────────────── */
        div[data-testid="stMetricValue"] { color: #10B981 !important; }
        div[data-testid="stMetricLabel"] { color: #94A3B8 !important; }
        div[data-testid="stMetricDelta"] { color: #E2E8F0 !important; }

        /* ── Buttons ───────────────────────────────────────────────── */
        .stButton > button, .stDownloadButton > button, .stLinkButton > a {
            background-color: #1E3A8A !important;
            color: #FFFFFF !important;
            border: 1px solid #334155 !important;
            border-radius: 8px;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            background-color: #1E40AF !important;
            transform: translateY(-1px);
        }

        /* ── Text / Number inputs ──────────────────────────────────── */
        .stTextInput input, .stNumberInput input, .stTextArea textarea,
        .stDateInput input, .stTimeInput input {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
            border: 1px solid #334155 !important;
        }
        /* Number-input +/- buttons */
        .stNumberInput button {
            background-color: #334155 !important;
            color: #E2E8F0 !important;
            border: 1px solid #475569 !important;
        }

        /* ── Selectbox / Multiselect (BaseWeb popover) ─────────────── */
        div[data-baseweb="select"] > div {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
            border-color: #334155 !important;
        }
        div[data-baseweb="select"] input,
        div[data-baseweb="select"] span,
        div[data-baseweb="select"] div {
            color: #E2E8F0 !important;
        }
        /* The dropdown menu (rendered in a portal at body level) */
        div[data-baseweb="popover"], ul[role="listbox"] {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
            border: 1px solid #334155 !important;
        }
        ul[role="listbox"] li,
        ul[role="listbox"] li[role="option"] {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
        }
        ul[role="listbox"] li:hover,
        ul[role="listbox"] li[aria-selected="true"] {
            background-color: #334155 !important;
        }
        /* Multiselect tags */
        span[data-baseweb="tag"] {
            background-color: #1E3A8A !important;
            color: #FFFFFF !important;
        }

        /* ── Sliders ───────────────────────────────────────────────── */
        .stSlider [data-baseweb="slider"] div { color: #E2E8F0 !important; }
        .stSlider [role="slider"] { background-color: #3B82F6 !important; }

        /* ── Radio / Checkbox ──────────────────────────────────────── */
        .stRadio label, .stCheckbox label { color: #E2E8F0 !important; }

        /* ── Tabs ──────────────────────────────────────────────────── */
        .stTabs [data-baseweb="tab-list"] {
            background-color: #1E293B !important;
            border-bottom: 1px solid #334155 !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #94A3B8 !important;
            background-color: transparent !important;
        }
        .stTabs [aria-selected="true"] {
            color: #E2E8F0 !important;
            border-bottom: 2px solid #3B82F6 !important;
        }
        [data-baseweb="tab-panel"] { background-color: transparent !important; }

        /* ── Expander ──────────────────────────────────────────────── */
        details, .streamlit-expander, [data-testid="stExpander"] {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }
        details summary, .streamlit-expanderHeader {
            color: #E2E8F0 !important;
            background-color: #1E293B !important;
        }
        .streamlit-expanderContent { background-color: #1E293B !important; }

        /* ── Status banners (info/success/warning/error) ───────────── */
        div[data-testid="stAlert"],
        div[data-baseweb="notification"] {
            color: #E2E8F0 !important;
            border-radius: 6px !important;
        }
        div[data-testid="stAlert"][kind="info"]    { background-color: #1E3A8A !important; border-left: 4px solid #3B82F6 !important; }
        div[data-testid="stAlert"][kind="success"] { background-color: #064E3B !important; border-left: 4px solid #10B981 !important; }
        div[data-testid="stAlert"][kind="warning"] { background-color: #78350F !important; border-left: 4px solid #F59E0B !important; }
        div[data-testid="stAlert"][kind="error"]   { background-color: #7F1D1D !important; border-left: 4px solid #EF4444 !important; }

        /* ── DataFrame / Table ─────────────────────────────────────── */
        .stDataFrame, [data-testid="stDataFrame"], [data-testid="stTable"] {
            background-color: #1E293B !important;
        }
        .stDataFrame [role="grid"], .stDataFrame [role="row"] {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
        }
        .dataframe, .dataframe td, .dataframe th {
            background-color: #1E293B !important;
            color: #E2E8F0 !important;
        }

        /* ── Forms / Cards / Custom ────────────────────────────────── */
        .stForm, [data-testid="stForm"] {
            background-color: #1E293B !important;
            border: 1px solid #334155 !important;
            border-radius: 8px !important;
        }
        .re-card { background: #1E293B !important; border-color: #334155 !important; color: #E2E8F0 !important; }

        /* ── Code blocks ───────────────────────────────────────────── */
        code, pre, .stCode {
            background-color: #0B1220 !important;
            color: #E2E8F0 !important;
        }

        /* ── Plotly chart container — keep transparent so chart bg shows ── */
        .stPlotlyChart, [data-testid="stPlotlyChart"] {
            background-color: transparent !important;
        }

        /* ── Sidebar — text & links ────────────────────────────────── */
        section[data-testid="stSidebar"] *,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] span {
            color: #E2E8F0 !important;
        }

        /* ── Custom data-source banner (sidebar) — dark variant ───── */
        .re-source-banner {
            background: #064E3B !important;
            border-left: 4px solid #10B981 !important;
            color: #ECFDF5 !important;
        }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.markdown("---")

# Navigation radio - always render, use session_state as default if exists
default_page_index = 0
if 'page' in st.session_state:
    pages = ["Inicio", "Pesquisar", "Watchlist", "Analise", "Sistema"]
    try:
        default_page_index = pages.index(st.session_state['page'])
    except ValueError:
        default_page_index = 0

page = st.sidebar.radio(
    "Navegacao",
    [
        "Inicio",
        "Pesquisar",
        "Watchlist",
        "Analise",
        "Sistema",
    ],
    index=default_page_index
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Acoes Rapidas")

# Quick actions
if st.sidebar.button("Pesquisar Tudo", width="stretch"):
    st.session_state.page = "Pesquisar"
    st.rerun()

if st.sidebar.button("Ver Watchlist", width="stretch"):
    st.session_state.page = "Watchlist"
    st.rerun()

if st.sidebar.button("Top Oportunidades", width="stretch"):
    st.session_state.page = "Inicio"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption(f"Dir: `{config.data_dir}`")
st.sidebar.caption("v3.0 — Enterprise Intelligence Engine")

# ── Data source health banner ───────────────────────────────────────────
try:
    from realestate_engine.database.repository import DatabaseRepository
    _repo = DatabaseRepository()
    _db_kind = "PostgreSQL" if "postgres" in config.database_url.lower() else (
        "SQLite (dev)" if config.database_url.startswith("sqlite") else "DB"
    )
    _total_real = len(_repo.get_clean_listings(limit=50000, include_sample=False))
    _is_dark = st.session_state.get('theme', 'light') == 'dark'
    _bg = "#064E3B" if _is_dark else "#ECFDF5"
    _fg = "#ECFDF5" if _is_dark else "#065F46"
    st.sidebar.markdown(
        f"<div class='re-source-banner' style='padding:8px;border-radius:6px;"
        f"background:{_bg};border-left:4px solid #10B981;color:{_fg};'>"
        f"<b>Fonte</b>: {_db_kind}<br/>"
        f"<b>Imoveis reais</b>: {_total_real:,}"
        f"</div>".replace(",", "."),
        unsafe_allow_html=True,
    )
    if _total_real == 0:
        st.sidebar.warning("Base de dados vazia. Execute o scraping real.")
except Exception as _e:
    st.sidebar.error(f"Data source unreachable: {_e}")

# ── Onboarding for first-time users ─────────────────────────────────────
if 'onboarding_completed' not in st.session_state:
    st.session_state.onboarding_completed = False

if not st.session_state.onboarding_completed:
    with st.expander("Bem-vindo ao Porto RE Engine!", expanded=True):
        st.markdown("""
        ### Guia Rápido
        
        **Inicio** - Visao geral do mercado com KPIs e melhores oportunidades
        
        **Pesquisar** - Encontre propriedades com filtros avancados
        
        **Watchlist** - Guarde propriedades para analise futura
        
        **Analise** - Mapa, analise de mercado e ferramentas de investimento
        
        **Sistema** - Estado do sistema, scraping e configuracoes
        
        ---
        
        **Dica:** Use o toggle de tema no topo da sidebar para mudar entre modo claro e escuro.
        """)
        
        if st.button("Entendi, comecar!", width="stretch"):
            st.session_state.onboarding_completed = True
            st.rerun()

# ── Route to pages ──────────────────────────────────────────────────────
if page == "Inicio":
    _render_view("realestate_engine.dashboard.views.overview", "render_overview")
elif page == "Pesquisar":
    _render_view("realestate_engine.dashboard.views.search", "render_search")
elif page == "Watchlist":
    _render_view("realestate_engine.dashboard.views.watchlist", "render_watchlist")
elif page == "Analise":
    # Sub-navigation for analysis pages
    analysis_pages = ["Mercado", "Mapa", "Investidor", "Melhores Deals (IA)"]
    default_analysis = st.session_state.get("analysis_page", analysis_pages[0])
    if default_analysis not in analysis_pages:
        default_analysis = analysis_pages[0]
    analysis_page = st.sidebar.radio(
        "Analise",
        analysis_pages,
        index=analysis_pages.index(default_analysis),
        key="analysis_page",
        label_visibility="collapsed"
    )
    if analysis_page == "Mercado":
        _render_view("realestate_engine.dashboard.views.market_analysis", "render_market_analysis")
    elif analysis_page == "Mapa":
        _render_view("realestate_engine.dashboard.views.map_view", "render_map_view")
    elif analysis_page == "Investidor":
        _render_view("realestate_engine.dashboard.views.investor_tools", "render_investor_tools")
    elif analysis_page == "Melhores Deals (IA)":
        _render_view("realestate_engine.dashboard.views.ai_deals", "render_ai_deals")
elif page == "Sistema":
    # Sub-navigation for system pages
    system_pages = ["Estado", "Scraping", "Score Audit", "Telegram", "Config", "Pipeline", "Qualidade", "Debug"]
    default_system = st.session_state.get("system_page", system_pages[0])
    if default_system not in system_pages:
        default_system = system_pages[0]
    system_page = st.sidebar.radio(
        "Sistema",
        system_pages,
        index=system_pages.index(default_system),
        key="system_page",
        label_visibility="collapsed"
    )
    if system_page == "Estado":
        _render_view("realestate_engine.dashboard.views.system", "render_system")
    elif system_page == "Scraping":
        _render_view("realestate_engine.dashboard.views.scraping_results", "render_scraping_results")
    elif system_page == "Score Audit":
        _render_view("realestate_engine.dashboard.views.score_audit", "render_score_audit")
    elif system_page == "Telegram":
        _render_view("realestate_engine.dashboard.views.telegram", "render_telegram")
    elif system_page == "Config":
        _render_view("realestate_engine.dashboard.views.config", "render_config")
    elif system_page == "Pipeline":
        _render_view("realestate_engine.dashboard.views.pipeline_status", "render_pipeline_status")
    elif system_page == "Qualidade":
        _render_view("realestate_engine.dashboard.views.data_quality_dashboard", "render_data_quality")
    elif system_page == "Debug":
        _render_view("realestate_engine.dashboard.views.debug_logs", "render_debug_logs")
