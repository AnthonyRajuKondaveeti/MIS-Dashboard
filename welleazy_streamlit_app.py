"""
Unified MIS Streamlit Dashboard
Welleazy & VeriRight MIS Systems
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from pathlib import Path
import io
import traceback
from dotenv import load_dotenv
import os
import yaml
from yaml.loader import SafeLoader
import bcrypt

# Load environment variables
load_dotenv()

def load_credentials():
    """Load credentials from st.secrets, then Environment Variables, then YAML config"""
    # 1. Try Streamlit Secrets (secrets.toml or Streamlit Cloud)
    try:
        if "credentials" in st.secrets:
            return st.secrets["credentials"]["usernames"]
    except Exception:
        pass

    # 2. Try Environment Variables (EC2/Server fallback)
    admin_pass = os.getenv('WELLEAZY_ADMIN_PASSWORD_HASH')
    manager_pass = os.getenv('WELLEAZY_MANAGER_PASSWORD_HASH')
    
    if admin_pass and manager_pass:
        return {
            "admin": {
                "email": os.getenv('WELLEAZY_ADMIN_EMAIL', 'admin@welleazy.com'),
                "name": os.getenv('WELLEAZY_ADMIN_NAME', 'Admin User'),
                "password": admin_pass
            },
            "manager": {
                "email": os.getenv('WELLEAZY_MANAGER_EMAIL', 'manager@welleazy.com'),
                "name": os.getenv('WELLEAZY_MANAGER_NAME', 'Manager User'),
                "password": manager_pass
            }
        }

    # 3. Fallback to local YAML config
    try:
        config_path = Path(__file__).parent / 'config_auth.yaml'
        if config_path.exists():
            with open(config_path) as file:
                config = yaml.load(file, Loader=SafeLoader)
                return config['credentials']['usernames']
    except Exception as e:
        st.error(f"⚠️ Failed to load credentials from YAML: {str(e)}")
        
    return {}

def verify_password(plain_password, hashed_password):
    """Verify password against bcrypt hash"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# Welleazy imports
from welleazy_pipeline import WelleazyMISPipeline
from welleazy_config import MISConfig

# Import Welleazy Generators
from welleazy_tat_mis import TATMISGenerator
from welleazy_pending_mis import PendingCaseMISGenerator
from welleazy_closure_tat_mis import ClosureTATMISGenerator
from welleazy_daily_mis import DailyMISGenerator

# VeriRight imports
from veriright_pipeline import VeriRightPipeline
from veriright_config import VeriRightConfig
from veriright_daily_mis import VeriRightDailyMISGenerator

from veriright_reports import (
    SUDReportGenerator, 
    SBIReportGenerator, 
    HDFCVcheckReportGenerator,
    HDFCITRReportGenerator,
    OverallMISReportGenerator,
    ClosedListReportGenerator
)

st.set_page_config(
    page_title="MIS Dashboard - Welleazy & VeriRight",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<style>
    /* Force consistent viewport */
    html, body {
        width: 100%;
        overflow-x: hidden;
    }
    
    /* Global Styles */
    .block-container { 
        padding-top: 2rem; 
        padding-bottom: 5rem;
        max-width: 100% !important;
        width: 100% !important;
    }
    h1, h2, h3 { font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; font-weight: 600; }
    
    /* Login Page Centered */
    .login-container {
        max-width: 420px !important;
        width: 100% !important;
        margin: 2rem auto 2rem auto !important;
        text-align: center;
        padding: 0 1rem;
        box-sizing: border-box;
    }
    
    .login-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }
    
    .login-subtitle {
        font-size: 1rem;
        opacity: 0.6;
        margin-bottom: 2rem;
        font-weight: 400;
    }
    
    /* Login Form Styling - Force consistent width */
    div[data-testid="stForm"] {
        max-width: 420px !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 2.5rem 2rem !important;
        border-radius: 16px !important;
        box-sizing: border-box !important;
    }
    
    div[data-testid="stForm"] h3 {
        text-align: center !important;
        margin-bottom: 1.5rem !important;
        font-size: 1.5rem !important;
        opacity: 0.9 !important;
    }
    
    div[data-testid="stForm"] input {
        background: rgba(255, 255, 255, 0.05) !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.85rem !important;
        font-size: 0.95rem !important;
        transition: all 0.3s ease !important;
    }
    
    /* Target the actual border container used by Streamlit */
    div[data-testid="stForm"] div[data-baseweb="input"],
    div[data-testid="stForm"] div[data-testid="stTextInputRootElement"] {
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        border-radius: 10px !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }

    /* Override all possible error/invalid/focus states */
    div[data-testid="stForm"] div[data-baseweb="input"]:focus-within,
    div[data-testid="stForm"] div[data-baseweb="input"][data-focus="true"],
    div[data-testid="stForm"] input:invalid,
    div[data-testid="stForm"] input[aria-invalid="true"],
    div[data-testid="stForm"] input:focus,
    div[data-testid="stForm"] input:focus-visible,
    div[data-testid="stForm"] input:active {
        border-color: rgba(255, 255, 255, 0.15) !important;
        box-shadow: none !important;
        outline: none !important;
    }
    
    /* Style password visibility toggle button */
    div[data-testid="stForm"] button[data-testid="baseButton-header"],
    div[data-testid="stForm"] button[kind="header"],
    div[data-testid="stForm"] .stTextInput button {
        background: transparent !important;
        border: none !important;
        color: rgba(255, 255, 255, 0.6) !important;
        padding: 0.5rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stForm"] button[data-testid="baseButton-header"]:hover,
    div[data-testid="stForm"] .stTextInput button:hover {
        color: rgba(255, 255, 255, 0.9) !important;
        background: rgba(255, 255, 255, 0.1) !important;
        border-radius: 6px !important;
    }
    
    /* Hide "Press Enter to submit form" text */
    div[data-testid="stForm"] .instructions,
    div[data-testid="stForm"] small,
    div[data-testid="stForm"] [class*="instructions"],
    div[data-testid="stForm"] [class*="InputInstructions"],
    div[data-testid="stForm"] .stTextInput > div > small,
    div[data-testid="stForm"] [data-testid="InputInstructions"],
    div[data-testid="stForm"] p small,
    div[data-testid="stForm"] .stTextInput small {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    
    /* Hide ALL possible status/running indicators */
    div[data-testid="stStatusWidget"],
    div[data-testid="stSidebarStatus"],
    .stStatusWidget,
    div[data-testid="stStatusIndicator"],
    div[data-testid="stSpinner"],
    .stSpinner,
    div[class*="spinner"],
    div[class*="loading"],
    [data-testid="stNotification"],
    .stAlert,
    div[role="alert"]:has-text("progress"),
    div[role="alert"]:has-text("loading"),
    div[role="status"]:has-text("Running") {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0 !important;
        width: 0 !important;
        overflow: hidden !important;
        pointer-events: none !important;
    }
    
    /* All Primary Buttons - Consistent styling */
    button[kind="primary"],
    button[kind="primaryFormSubmit"],
    div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
        width: 100% !important;
        padding: 0.85rem !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-top: 1rem !important;
        transition: all 0.3s ease !important;
        cursor: pointer !important;
    }
    
    button[kind="primary"]:hover,
    button[kind="primaryFormSubmit"]:hover,
    div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(168, 85, 247, 0.4) !important;
    }
    
    /* Sidebar Buttons */
    .stButton > button {
        width: 100% !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
    }
    
    /* User Profile in Sidebar */
    .user-profile {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(168, 85, 247, 0.1) 100%);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid rgba(128, 128, 128, 0.2);
    }
    
    .user-name {
        font-size: 1.1rem;
        font-weight: 600;
    }
    
    /* KPI Cards */
    .kpi-card {
        background-color: transparent; 
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(128, 128, 128, 0.2); 
        text-align: center;
        transition: transform 0.2s;
    }
    .kpi-card:hover { 
        transform: translateY(-2px); 
        border-color: rgba(128, 128, 128, 0.5);
    }
    
    .big-metric { font-size: 3rem; font-weight: 800; margin: 0; line-height: 1.2; }
    .metric-label { font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; opacity: 0.8; }
    .metric-sub { font-size: 0.875rem; margin-top: 4px; opacity: 0.6; }
    
    /* Status Colors */
    .status-excellent { color: #10b981; }
    .status-warning { color: #f59e0b; }
    .status-critical { color: #ef4444; }
    
    /* Dividers */
    .divider { border-top: 2px solid rgba(128, 128, 128, 0.2); margin: 2.5rem 0; }
    
    /* Filters */
    .stDateInput > label, .stMultiSelect > label { font-size: 1rem; font-weight: 600; }
    
    /* Mobile Responsive */
    @media (max-width: 768px) {
        .login-container {
            max-width: 90% !important;
            padding: 0 0.5rem;
        }
        
        div[data-testid="stForm"] {
            max-width: 100% !important;
            padding: 1.5rem 1rem !important;
        }
        
        .login-title {
            font-size: 2rem;
        }
        
        .big-metric {
            font-size: 2rem;
        }
    }
</style>

""", unsafe_allow_html=True)

def init_state():
    """Initialize session state for both Welleazy and VeriRight"""
    # System selector
    if 'selected_system' not in st.session_state:
        st.session_state.selected_system = 'Welleazy'
    
    # Welleazy state
    for key in ['pipeline', 'normalized_data', 'global_clients', 'global_min_date', 'global_max_date']:
        if key not in st.session_state:
            st.session_state[key] = None
    
    # VeriRight state
    for key in ['vr_pipeline', 'vr_normalized_data', 'vr_clients', 'vr_min_date', 'vr_max_date']:
        if key not in st.session_state:
            st.session_state[key] = None

def filter_dataframe(df, date_range, selected_clients):
    """Apply date and client filters to dataframe"""
    if df is None:
        return None
    
    filtered = df.copy()
    
    # Apply date filter
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        # Ensure case_received_date is datetime
        if not pd.api.types.is_datetime64_any_dtype(filtered['case_received_date']):
             filtered['case_received_date'] = pd.to_datetime(filtered['case_received_date'], errors='coerce')
             
        filtered = filtered[
            (filtered['case_received_date'].dt.date >= start_date) & 
            (filtered['case_received_date'].dt.date <= end_date)
        ]
    
    # Apply client filter
    if selected_clients:
        filtered = filtered[filtered['client_name'].isin(selected_clients)]
    
    return filtered

def render_filters(key_prefix):
    """Render elegant filters for Date and Client"""
    if st.session_state.normalized_data is None:
        return None, None

    df = st.session_state.normalized_data
    
    # Get defaults from global state (set during process)
    min_date = st.session_state.global_min_date
    max_date = st.session_state.global_max_date
    all_clients = st.session_state.global_clients
    
    if min_date is None or max_date is None:
         min_date = datetime.now().date()
         max_date = datetime.now().date()
    
    st.markdown("### Filter Data")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"date_{key_prefix}",
            format="DD/MM/YYYY"
        )
    
    with col2:
        # Client Filter - "Select All" Logic by default (Empty = All)
        selected_clients = st.multiselect(
            "Select Clients",
            options=all_clients,
            default=[], # Default to empty, which implies ALL in our logic below
            key=f"client_{key_prefix}",
            placeholder="Search specific clients"
        )
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    return date_range, selected_clients

def render_veriright_filters(key_prefix):
    """Render filters for VeriRight Date and Client"""
    if st.session_state.vr_normalized_data is None:
        return None, None

    df = st.session_state.vr_normalized_data
    
    # Get defaults from VeriRight state
    min_date = st.session_state.vr_min_date
    max_date = st.session_state.vr_max_date
    all_clients = st.session_state.vr_clients
    
    if min_date is None or max_date is None:
         min_date = datetime.now().date()
         max_date = datetime.now().date()
    
    st.markdown("### Filter Data")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
            key=f"vr_date_{key_prefix}",
            format="DD/MM/YYYY"
        )
    
    with col2:
        selected_clients = st.multiselect(
            "Select Clients",
            options=all_clients,
            default=[],
            key=f"vr_client_{key_prefix}",
            placeholder="Search specific clients"
        )
    
    st.markdown("<div style='margin-bottom: 2rem;'></div>", unsafe_allow_html=True)
    return date_range, selected_clients


def filter_veriright_dataframe(df, date_range, selected_clients):
    """Filter VeriRight dataframe by date and clients"""
    if df is None or df.empty:
        return df
    
    filtered = df.copy()
    
    # Apply date filter
    if date_range and len(date_range) == 2:
        start_date, end_date = date_range
        if not pd.api.types.is_datetime64_any_dtype(filtered['case_received_date']):
             filtered['case_received_date'] = pd.to_datetime(filtered['case_received_date'], errors='coerce')
             
        filtered = filtered[
            (filtered['case_received_date'].dt.date >= start_date) & 
            (filtered['case_received_date'].dt.date <= end_date)
        ]
    
    # Apply client filter
    if selected_clients:
        filtered = filtered[filtered['client_name'].isin(selected_clients)]
    
    return filtered


def calc_kpis(df):
    """Calculate KPIs from a (filtered) dataframe"""
    if df is None or df.empty:
        return None
    
    # Total cases
    total = len(df)
    
    # Closure rate
    closed_statuses = MISConfig.get_status_filter('closed_cases')
    norm_closed = [MISConfig.normalize_status_value(s) for s in closed_statuses]
    status_norm = df['case_status'].apply(MISConfig.normalize_status_value)
    closed = status_norm.isin(norm_closed).sum()
    closure_rate = (closed / total * 100) if total > 0 else 0
    
    # TAT Analysis - Only for non-closed cases with appointment dates
    avg_tat = 0
    high_tat = 0
    
    # Calculate TAT only for non-closed cases
    df_tat = df.copy()
    
    # Filter out closed cases
    closed_statuses = MISConfig.get_status_filter('closed_cases')
    norm_closed = [MISConfig.normalize_status_value(s) for s in closed_statuses]
    status_norm_tat = df_tat['case_status'].apply(MISConfig.normalize_status_value)
    df_tat = df_tat[~status_norm_tat.isin(norm_closed)].copy()
    
    # Ensure appointment_date is datetime
    if 'appointment_date' in df_tat.columns and not df_tat.empty:
        if not pd.api.types.is_datetime64_any_dtype(df_tat['appointment_date']):
            df_tat['appointment_date'] = pd.to_datetime(df_tat['appointment_date'], errors='coerce')
        
        # Filter for cases with valid appointment dates
        df_with_appt = df_tat[df_tat['appointment_date'].notna()].copy()
        
        if not df_with_appt.empty:
            # Calculate TAT: Current Date - Appointment Date
            current_date = pd.Timestamp.now().normalize()
            df_with_appt['tat_days'] = (current_date - df_with_appt['appointment_date']).dt.days
            
            # Handle negative TATs (future appointments)
            df_with_appt['tat_days'] = df_with_appt['tat_days'].clip(lower=0)
            
            # Calculate metrics
            avg_tat = df_with_appt['tat_days'].mean()
            high_tat = int((df_with_appt['tat_days'] > MISConfig.TAT_THRESHOLD).sum())
    
    # Pending - As per documentation (specific statuses only)
    # Appointment Missed, Call-later, Fresh case, Waiting for DC confirmation
    pending_statuses = MISConfig.get_status_filter('pending_mis')
    norm_pending = [MISConfig.normalize_status_value(s) for s in pending_statuses]
    pending = status_norm.isin(norm_pending).sum()
    
    return {
        'total': total,
        'closure_rate': round(closure_rate, 1),
        'closed': int(closed),
        'avg_tat': round(avg_tat, 1),
        'high_tat': high_tat,
        'pending': int(pending)
    }

def sidebar():
    with st.sidebar:
        # System Selector at the top
        st.markdown("### 📊 MIS System")
        system = st.radio(
            "Select System:",
            options=['Welleazy', 'VeriRight'],
            index=0 if st.session_state.selected_system == 'Welleazy' else 1,
            horizontal=True,
            label_visibility="collapsed"
        )
        
        # Update selected system
        if system != st.session_state.selected_system:
            st.session_state.selected_system = system
            st.rerun()
        
        st.markdown("---")
        
        # Render appropriate sidebar based on selection
        if st.session_state.selected_system == 'Welleazy':
            _welleazy_sidebar()
        else:
            _veriright_sidebar()

        # User info and logout at the top
        if st.session_state.get('authenticated', False):
            # st.markdown("""
            # <div class='user-profile'>
            #     <div class='user-name'>👤 {}</div>
            # </div>
            # """.format(st.session_state.get('name', 'User')), unsafe_allow_html=True)
            
            if st.button("Logout", key="logout_btn", type="secondary", use_container_width=True):
                # Preserve data state across logout/login
                preserved_data = {
                    'normalized_data': st.session_state.get('normalized_data'),
                    'pipeline': st.session_state.get('pipeline'),
                    'global_clients': st.session_state.get('global_clients'),
                    'global_min_date': st.session_state.get('global_min_date'),
                    'global_max_date': st.session_state.get('global_max_date'),
                    'api_load_attempted': st.session_state.get('api_load_attempted'),
                    'selected_system': st.session_state.get('selected_system'),
                    'vr_normalized_data': st.session_state.get('vr_normalized_data'),
                    'vr_pipeline': st.session_state.get('vr_pipeline'),
                    'vr_clients': st.session_state.get('vr_clients'),
                    'vr_min_date': st.session_state.get('vr_min_date'),
                    'vr_max_date': st.session_state.get('vr_max_date'),
                }
                
                # Clear ALL session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                
                # Restore preserved data
                for key, value in preserved_data.items():
                    if value is not None:
                        st.session_state[key] = value
                
                # Redirect to login page
                st.rerun()
        
        # st.markdown("---")


def _welleazy_sidebar():
    """Welleazy sidebar content"""
    st.markdown("### Welleazy MIS")
    st.caption("Executive Dashboard")
    st.markdown("---")
    
    # Show data status
    if st.session_state.normalized_data is not None:
        # st.success(f"✓ {len(st.session_state.normalized_data):,} records loaded")
        
        # Option to reload from API
        if st.button("🔄 Reload from API", type="primary", use_container_width=True):
            st.session_state.normalized_data = None
            st.session_state.pipeline = None
            st.session_state.api_load_attempted = False  # Reset to trigger auto-load
            st.rerun()
        
        st.markdown("---")
    else:
        # No data loaded - show load button
        st.info("📊 No data loaded")
    
    # File upload option (alternative to API)
    uploaded = st.file_uploader("Upload CRM Data (Optional)", type=['xlsx', 'xls', 'csv'], key="welleazy_upload")
    
    # Process button logic
    should_process = False
    use_api = False
    
    if uploaded:
        st.success(f"✓ Uploaded: {uploaded.name}")
        should_process = st.button("🚀 Process Uploaded Data", type="primary", use_container_width=True, key="welleazy_process_file")
    elif st.session_state.normalized_data is None:
        # Show button to load from API when no data is loaded
        use_api = st.button("🌐 Load Data from API", type="primary", use_container_width=True, key="welleazy_process_api")
        should_process = use_api
    
    if should_process:
        try:
            # Create pipeline with either BytesIO buffer or API endpoint
            if use_api:
                api_endpoint = os.getenv('WELLEAZY_API_ENDPOINT', 'http://api.welleazy.com/PhysicalMedicalMISReport')
                # st.info(f"Fetching data from: {api_endpoint}")
                pipeline = WelleazyMISPipeline(api_endpoint=api_endpoint)
            else:
                # Process uploaded file in-memory without temp files
                file_buffer = io.BytesIO(uploaded.getvalue())
                file_ext = uploaded.name.lower().split('.')[-1]
                
                # Read directly from buffer based on file type
                if file_ext == 'csv':
                    df_raw = pd.read_csv(file_buffer, low_memory=False)
                else:  # xlsx or xls
                    df_raw = pd.read_excel(file_buffer)
                
                # Create pipeline with dummy path (won't be used)
                pipeline = WelleazyMISPipeline(data_path="uploaded")
                pipeline.raw_data = df_raw
                
            pipeline._ingest_data()
            pipeline._normalize_data()
            
            st.session_state.pipeline = pipeline
            st.session_state.normalized_data = pipeline.normalized_data
            
            # Initialize global bounds for filters
            df = st.session_state.normalized_data
            st.session_state.global_clients = sorted(df['client_name'].dropna().unique().tolist())
            
            # Handle Date Parsing for bounds
            if not pd.api.types.is_datetime64_any_dtype(df['case_received_date']):
                df['case_received_date'] = pd.to_datetime(df['case_received_date'], errors='coerce')
                
            min_d = df['case_received_date'].min()
            max_d = df['case_received_date'].max()
            
            if pd.isna(min_d) or pd.isna(max_d):
                 st.session_state.global_min_date = datetime.now().date()
                 st.session_state.global_max_date = datetime.now().date()
            else:
                 st.session_state.global_min_date = min_d.date()
                 st.session_state.global_max_date = max_d.date()
            
            st.success("✓ Data Processed Successfully!")
            st.rerun()
        except Exception as e:
            # User-friendly error messages
            if "500" in str(e) or "Internal Server Error" in str(e):
                st.error("🔴 API Server Error")
                st.warning("""
                The API server is currently experiencing issues (HTTP 500 error). 
                This is a server-side problem and not related to your request.
                
                **Suggestions:**
                - Try uploading an Excel/CSV file instead
                - Wait a few minutes and try the API again
                - Contact the API administrator if the issue persists
                """)
            elif "Timeout" in str(e) or "timed out" in str(e):
                st.error("⏱️ Request Timeout")
                st.warning("""
                    The API request took too long to respond.
                    
                    **Suggestions:**
                    - Check your internet connection
                    - Try uploading an Excel/CSV file instead
                    - Try the API again later
                    """)
            elif "Connection" in str(e) or "Failed to connect" in str(e):
                st.error("🌐 Connection Error")
                st.warning("""
                    Could not connect to the API server.
                    
                    **Suggestions:**
                    - Check your internet connection
                    - Verify the API URL is correct
                    - Try uploading an Excel/CSV file instead
                    """)
            else:
                st.error(f"Error: {str(e)}")
                with st.expander("View Technical Details"):
                    import traceback
                    st.code(traceback.format_exc())
    
    st.markdown("---")
    # if st.session_state.normalized_data is not None:
    #      st.info(f"📊 Loaded {len(st.session_state.normalized_data)} records")


def _veriright_sidebar():
    """VeriRight sidebar content"""
    st.markdown("### VeriRight MIS")
    st.caption("Client Performance Dashboard")
    st.markdown("---")
    
    # Multiple file upload for VeriRight (HDFC Life, SBI Life, etc.)
    uploaded_files = st.file_uploader(
        "Upload Data Files",
        type=['xlsx', 'xls', 'csv'],
        accept_multiple_files=True,
        key="veriright_upload",
        help="Upload HDFC Life, SBI Life, and other client files (Excel or CSV)"
    )
    
    if uploaded_files:
        st.success(f"✓ {len(uploaded_files)} file(s) uploaded")
        
        # Show uploaded file names
        with st.expander("📁 Uploaded Files"):
            for f in uploaded_files:
                st.write(f"• {f.name}")
        
        if st.button("🚀 Process Data", type="primary", use_container_width=True, key="veriright_process"):
            try:
                # Process uploaded files in-memory
                file_buffers = {}
                for uploaded in uploaded_files:
                    file_buffers[uploaded.name] = io.BytesIO(uploaded.getvalue())
                
                # Process through pipeline with in-memory buffers
                pipeline = VeriRightPipeline()
                normalized_data = pipeline.load_from_files(file_buffers)
                
                if normalized_data is not None and not normalized_data.empty:
                    st.session_state.vr_pipeline = pipeline
                    st.session_state.vr_normalized_data = normalized_data
                    
                    # Initialize filter bounds
                    df = normalized_data
                    st.session_state.vr_clients = sorted(df['client_name'].dropna().unique().tolist())
                    
                    if 'case_received_date' in df.columns:
                        min_d = df['case_received_date'].min()
                        max_d = df['case_received_date'].max()
                        
                        if pd.notna(min_d) and pd.notna(max_d):
                            st.session_state.vr_min_date = min_d.date()
                            st.session_state.vr_max_date = max_d.date()
                    
                    st.success("✓ VeriRight Data Processed!")
                    st.rerun()
                else:
                    st.error("No data could be processed from uploaded files")
                        
            except Exception as e:
                st.error(f"Error processing VeriRight data: {str(e)}")
                import traceback
                st.code(traceback.format_exc())
    
    st.markdown("---")
    if st.session_state.vr_normalized_data is not None:
        st.info(f"Loaded {len(st.session_state.vr_normalized_data)} records")


def overview_tab():
    if st.session_state.normalized_data is None:
        st.info("Please upload data in the sidebar to begin.")
        return

    # Header
    # st.markdown("## Executive Overview")
    # st.markdown(f"*Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")

    # 1. Render Filters
    date_range, clients = render_filters("overview")
    
    # 2. Filter Data
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
        
    # 3. Calculate KPIs
    kpis = calc_kpis(df)
    
    # Header
    # st.markdown("## Executive Overview")
    # st.markdown(f"*Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Key Metrics Row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='metric-label'>Total Cases</div>
            <div class='big-metric'>{kpis['total']:,}</div>
            <div class='metric-sub'>Closed: {kpis['closed']:,} | Pending: {kpis['pending']:,}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        status = "excellent" if kpis['closure_rate'] >= 90 else "warning" if kpis['closure_rate'] >= 80 else "critical"
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='metric-label'>Closure Rate</div>
            <div class='big-metric status-{status}'>{kpis['closure_rate']}%</div>
            <div class='metric-sub'>Target: 85% | Excellent: 90%+</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        status = "excellent" if kpis['high_tat'] == 0 else "warning" if kpis['high_tat'] < 50 else "critical"
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='metric-label'>High TAT Cases</div>
            <div class='big-metric status-{status}'>{kpis['high_tat']}</div>
            <div class='metric-sub'>All Active Cases &gt; 3 days</div>
        </div>
        """, unsafe_allow_html=True)
        # st.caption("💡 ALL non-closed cases with TAT > 3 days")
        # st.caption("💡 This includes ALL non-closed cases, not just 'Medical Done' status")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # High TAT Calculation Breakdown
    with st.expander("📊 High TAT Calculation Details", expanded=False):
        closed_statuses = MISConfig.get_status_filter('closed_cases')
        norm_closed = [MISConfig.normalize_status_value(s) for s in closed_statuses]
        status_norm = df['case_status'].apply(MISConfig.normalize_status_value)
        
        total_cases = len(df)
        closed_count = status_norm.isin(norm_closed).sum()
        non_closed = total_cases - closed_count
        
        # Count cases with appointment dates (non-closed)
        df_temp = df[~status_norm.isin(norm_closed)].copy()
        df_temp['appointment_date'] = pd.to_datetime(df_temp['appointment_date'], errors='coerce')
        cases_with_appt = df_temp['appointment_date'].notna().sum()
        
        # Calculate TAT for breakdown
        df_with_appt = df_temp[df_temp['appointment_date'].notna()].copy()
        if not df_with_appt.empty:
            current_date = pd.Timestamp.now().normalize()
            df_with_appt['tat_days'] = (current_date - df_with_appt['appointment_date']).dt.days
            df_with_appt['tat_days'] = df_with_appt['tat_days'].clip(lower=0)
            
            tat_0_3 = (df_with_appt['tat_days'] <= 3).sum()
            tat_above_3 = (df_with_appt['tat_days'] > 3).sum()
            
            st.markdown(f"""
            **Calculation Logic:**
            1. Total cases in view: **{total_cases:,}**
            2. Closed cases (excluded): **{closed_count:,}**
            3. Non-closed cases: **{non_closed:,}**
            4. Non-closed with appointment date: **{cases_with_appt:,}**
            5. Cases with TAT ≤ 3 days: **{tat_0_3:,}**
            6. **Cases with TAT > 3 days: {tat_above_3:,}** ← High TAT Count
            
            ---
            **Formula:** High TAT = Non-closed cases with (Current Date - Appointment Date) > 3 days
            
            **Note:** This includes ALL non-closed cases with appointments, not just "Medical Done - Report Awaited" status.
            """)
            
            # Show breakdown by case status
            st.markdown("### High TAT Cases by Status")
            high_tat_cases = df_with_appt[df_with_appt['tat_days'] > 3].copy()
            status_breakdown = high_tat_cases['case_status'].value_counts().reset_index()
            status_breakdown.columns = ['Case Status', 'Count']
            st.dataframe(status_breakdown, use_container_width=True, hide_index=True)
            
            # Show detailed list of high TAT cases
            st.markdown("### Detailed List of High TAT Cases")
            display_cols = ['client_name', 'customer_name', 'case_id', 'appointment_date', 
                          'tat_days', 'case_status', 'dc_name', 'dc_city']
            available_cols = [col for col in display_cols if col in high_tat_cases.columns]
            
            high_tat_display = high_tat_cases[available_cols].sort_values('tat_days', ascending=False)
            
            st.dataframe(
                high_tat_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "appointment_date": st.column_config.DateColumn("Appointment Date", format="DD/MM/YYYY"),
                    "tat_days": st.column_config.NumberColumn("TAT Days", format="%d"),
                }
            )
        else:
            st.info("No cases with appointment dates found.")

    # 1. Trend Analysis
    st.markdown("### Trend Analysis")
    if 'case_received_date' in df.columns:
        # Clean date and aggregate
        daily_trend = df.groupby(df['case_received_date'].dt.date).size().reset_index(name='Received')
        daily_trend.columns = ['Date', 'Received']
        
        # Calculate Closed counts by received date (approximate flow) or actual closed date if available
        # For simplicity in this view without changing agg logic, we show Volume Trend
        
        fig_trend = px.line(daily_trend, x='Date', y='Received', 
                          title='Daily Case Volume',
                          markers=True, line_shape='spline')
        fig_trend.update_traces(line_color='#6366f1', line_width=3)
        fig_trend.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Cases",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_trend, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    
    # 2. Detailed Breakdown Charts
    # Switched to Horizontal Bar Chart for better readability of long status labels
    st.markdown("### Case Status Distribution")
    status_counts = df['case_status'].value_counts().head(10)
    
    fig = px.bar(
        x=status_counts.values,
        y=status_counts.index,
        orientation='h',
        text=status_counts.values,
        title="",
        color=status_counts.values,
        color_continuous_scale='Viridis'
    )
    
    fig.update_traces(
        textposition='outside',
        texttemplate='%{text}',
    )
    
    fig.update_layout(
        height=500,
        xaxis_title="Number of Cases",
        yaxis_title="",
        yaxis=dict(autorange="reversed"),
        showlegend=False,
        margin=dict(t=20, b=20, l=0, r=40),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis_showgrid=True,
        xaxis_gridcolor='rgba(128, 128, 128, 0.2)',
    )
    st.plotly_chart(fig, use_container_width=True)

def client_tab():
    st.markdown("## Client Performance")
    if st.session_state.normalized_data is None:
        st.info("No data loaded.")
        return

    # 1. Filters
    date_range, clients = render_filters("clients")
    
    # 2. Filter Data
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty:
         st.warning("No data found")
         return
         
    # 3. Generate Client Metrics (Use logic similar to Daily MIS, or simplified)
    # Simplified aggregate logic for responsiveness
    
    # Group by Client
    client_stats = []
    
    # Pre-calculate counts
    # Total Received
    received = df.groupby('client_name')['case_id'].count()
    
    # Closed
    closed_statuses = MISConfig.get_status_filter('closed_cases')
    norm_closed = [MISConfig.normalize_status_value(s) for s in closed_statuses]
    status_norm = df['case_status'].apply(MISConfig.normalize_status_value)
    
    closed_df = df[status_norm.isin(norm_closed)]
    closed = closed_df.groupby('client_name')['case_id'].count()
    
    # Merge
    all_clients = sorted(list(set(received.index) | set(closed.index)))
    
    for client in all_clients:
        r = received.get(client, 0)
        c = closed.get(client, 0)
        rate = (c / r * 100) if r > 0 else 0
        
        client_stats.append({
            'Client': client,
            'Received': r,
            'Closed': c,
            'Rate': round(rate, 1)
        })
        
    client_df = pd.DataFrame(client_stats).sort_values('Received', ascending=False)
    
    # Top 10 Display
    st.markdown("### Top 10 Clients by Volume")
    
    for _, row in client_df.head(10).iterrows():
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1: st.markdown(f"**{row['Client']}**")
        with col2: st.metric("Received", row['Received'])
        with col3: st.metric("Closed", row['Closed'])
        with col4: st.metric("Rate", f"{row['Rate']}%")
        with col5:
            if row['Rate'] >= 90: st.success("Excellent")
            elif row['Rate'] >= 80: st.warning("Good")
            else: st.error("Alert")
        st.markdown("---")
        
    # Chart
    st.markdown("### Client Closure Performance")
    if not client_df.empty:
        # Create a more advanced layout
        fig = px.bar(
            client_df.head(20), # Show top 20
            x='Client',
            y='Rate',
            color='Rate',
            color_continuous_scale=['#dc2626', '#fbbf24', '#059669'], # Red -> Yellow -> Green
            text='Rate',
            custom_data=['Received', 'Closed']
        )
        fig.update_traces(
            texttemplate='%{text}%', 
            textposition='outside',
            hovertemplate="<b>%{x}</b><br>Closure Rate: %{y}%<br>Received: %{customdata[0]}<br>Closed: %{customdata[1]}"
        )
        fig.add_hline(y=85, line_dash="dash", line_color="#4b5563", annotation_text="Target: 85%", annotation_position="bottom right")
        
        fig.update_layout(
            height=500,
            xaxis_title="", 
            yaxis_title="Closure Rate (%)",
            xaxis_tickangle=-45,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            yaxis=dict(range=[0, 105]),
            xaxis=dict(showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

def operations_tab():
    st.markdown("## Operations Performance")
    if st.session_state.normalized_data is None:
        st.info("No data loaded.")
        return

    # 1. Filters
    date_range, clients = render_filters("operations")
    
    # 2. Filter Data
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty: return
    
    # DC Performance
    st.markdown("### Diagnostic Center Performance by City")
    
    if 'dc_city' not in df.columns:
        st.error("DC City column missing")
        return

    dc_data = []
    for city in df['dc_city'].dropna().unique():
        city_df = df[df['dc_city'] == city]
        
        # Calculate closure for this city
        # Note: Using simplified closure logic here for speed
        closed_statuses = MISConfig.get_status_filter('closed_cases')
        norm_closed = [MISConfig.normalize_status_value(s) for s in closed_statuses]
        status_norm = city_df['case_status'].apply(MISConfig.normalize_status_value)
        closed = status_norm.isin(norm_closed).sum()
        rate = (closed / len(city_df) * 100) if len(city_df) > 0 else 0
        
        dc_data.append({
            'City': city,
            'Cases': len(city_df),
            'Closure': round(rate, 1)
        })
    
    dc_df = pd.DataFrame(dc_data).sort_values('Cases', ascending=False).head(10)
    
    if dc_df.empty:
        st.info("No DC data available in this range.")
        return

    # Display Rows
    for _, row in dc_df.iterrows():
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        with col1: st.markdown(f"**{row['City']}**")
        with col2: st.metric("Cases", row['Cases'])
        with col3:
            status = '🟢' if row['Closure'] >= 90 else '🟡' if row['Closure'] >= 85 else '🔴'
            st.metric("Closure", f"{status} {row['Closure']}%")
        with col4: st.progress(row['Closure'] / 100)
        st.markdown("---")
    
    # Chart
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Cases by Location")
        fig = px.bar(dc_df, x='City', y='Cases', color='Cases', color_continuous_scale='Blues')
        fig.update_layout(
            height=400, 
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title=""
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Closure Rate by Location")
        fig = px.bar(dc_df, x='City', y='Closure', color='Closure', 
                      color_continuous_scale=['#ef4444', '#f59e0b', '#10b981'])
        fig.add_hline(y=85, line_dash="dash", annotation_text="Target")
        fig.update_layout(
            height=400, 
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis_title="",
            yaxis=dict(range=[0, 105])
        )
        st.plotly_chart(fig, use_container_width=True)

def tat_tab():
    st.markdown("## TAT MIS Report")
    st.caption("📋 Shows only cases with status: 'Medical Done - Report Awaited' | For all high TAT cases, see Overview tab")
    
    if st.session_state.normalized_data is None:
        st.info("No data loaded.")
        return

    # 1. Filters
    date_range, clients = render_filters("tat")
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty: return

    # 2. Generate Report
    gen = TATMISGenerator(df)
    report_df = gen.generate()
    summary = gen.get_summary()

    if report_df.empty:
        st.warning("""No cases found with 'Medical Done-Report Awaited' status matching the filters.
        
        💡 **Tip:** This report only shows cases specifically in 'Medical Done - Report Awaited' status.
        To see ALL high TAT cases across all statuses, check the **Overview** tab.""")
        return

    # 3. Summary Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Cases", summary.get('total_cases', 0))
    col2.metric("High TAT", summary.get('high_tat_cases', 0))
    col3.metric("Avg TAT", f"{summary.get('avg_tat', 0):.1f}d")
    col4.metric("Max TAT", f"{summary.get('max_tat', 0)}d")
    
    st.markdown("---")

    # Removed TAT Distribution as per user request
    
    st.markdown("---")
    
    # 4. View Options
    col1, col2 = st.columns([1, 3])
    with col1:
        show_high = st.checkbox("Show only High TAT (>3d)", True)
    
    filtered_view = report_df[report_df['high_tat']] if show_high else report_df
    
    st.dataframe(
        filtered_view,
        use_container_width=True,
        height=500,
        column_config={
            "tat_days": st.column_config.NumberColumn("TAT (days)", format="%d"),
            "high_tat": st.column_config.CheckboxColumn("High TAT")
        }
    )
    
    # 5. Download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        report_df.to_excel(writer, index=False, sheet_name='TAT MIS')
    
    st.download_button(
        "📥 Download Report",
        data=buffer.getvalue(),
        file_name=f"TAT_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def pending_tab():
    st.markdown("## Pending Case MIS")
    if st.session_state.normalized_data is None: return

    date_range, clients = render_filters("pending")
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty: return
    
    gen = PendingCaseMISGenerator(df)
    report = gen.generate()
    summary = gen.get_summary()
    
    if report.empty:
        st.warning("No pending cases found.")
        return
        
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Pending", summary.get('total_pending', 0))
    col2.metric("Critical Cases", summary.get('critical_cases', 0))
    col3.metric("Statuses", len(summary.get('by_status', {})))
    
    st.markdown("---")
    st.dataframe(report, use_container_width=True, height=400)
    
    # Generate Excel in memory without temp files
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        report.to_excel(writer, index=False, sheet_name='Pending MIS')
    
    st.download_button(
        "📥 Download Report",
        data=buffer.getvalue(),
        file_name=f"Pending_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def closure_tab():
    st.markdown("## Closure TAT MIS")
    
    # 0. TAT Calculation Details
    with st.expander("📊 TAT Calculation Details"):
        st.markdown("""
        ### Closure TAT Calculation
        **Formula:** `NETWORKDAYS(Appointment Date, Case Completion Date) - 1`
        
        **Explanation:**
        - Counts **working days only** (Monday to Saturday)
        - Excludes **Sundays** and **Indian public holidays**
        - Subtracts 1 as per the standard formula
        - Example: Appointment on Monday, Completion on Wednesday = 2 working days - 1 = **1 day TAT**
        
        **Capping Rule:** Any TAT ≥ 3 is capped at **3 days**
        
        ---
        
        ### Scheduled TAT Calculation
        **Formula:** `Appointment Fixed Date - Case Received Date`
        
        **Explanation:**
        - Counts **calendar days** (not working days)
        - Measures time from when case was received to when appointment was fixed
        - Example: Received on 10th, Fixed on 12th = **2 days TAT**
        
        **Capping Rule:** Any TAT ≥ 3 is capped at **3 days**
        
        """)
        
    if st.session_state.normalized_data is None: return
    
    date_range, clients = render_filters("closure")
    
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty: return
    
    gen = ClosureTATMISGenerator(df)
    closure_df, schedule_df = gen.generate()
    
    if closure_df.empty:
        st.warning("No closed cases found in this range.")
        return
        
    # NEW: TAT Breakdown Analysis
    st.markdown("### Closure & Scheduled TAT Breakdown")
    
    # Calculate Buckets dynamically
    # Note: We need the raw data with TATs, which 'gen' calculates internally but doesn't expose raw.
    # We will re-calculate for visualization or access internal if possible.
    # WelleazyClosureTATMISGenerator filters internally. 
    # Let's perform a lightweight recalc here for the graph.
    
    # Re-use logic for TAT bucket calc
    tat_data = df.copy()
    
    # Helper to clean date
    def to_dt(s): return pd.to_datetime(s, errors='coerce')
    
    # Filter closed similar to generator
    closed_statuses = MISConfig.get_status_filter('closed_cases')
    norm_closed = [MISConfig.normalize_status_value(s) for s in closed_statuses]
    status_norm = tat_data['case_status'].apply(MISConfig.normalize_status_value)
    tat_data = tat_data[status_norm.isin(norm_closed)]
    
    if not tat_data.empty:
        # We need holidays for perfect networkdays, but for visualization approximate is okay 
        # OR we can assume `closure_tat` column might exist if pipeline added it? 
        # Pipeline doesn't add it globally. Generator does.
        # Let's use the generator's internal method if accessible or replicate simply.
        # Replicating simple diff for speed in "Scheduled", strict for "Closure" is hard without holidays.
        # BUT: The pipeline might have normalized it? No.
        # Let's just do a simple business day calc for visualization or use calendar days as proxy if acceptible?
        # BETTER: Use valid logic.
        
        # Recalculate Closure TAT (Simplified Business Days: np.busday_count)
        tat_data['case_completion_date'] = to_dt(tat_data['case_completion_date'])
        tat_data['appointment_date'] = to_dt(tat_data['appointment_date'])
        tat_data = tat_data.dropna(subset=['case_completion_date', 'appointment_date'])
        
        # Calculate stats
        tats = []
        for _, row in tat_data.iterrows():
            try:
                # Simple business day calc (Mon-Fri)
                days = np.busday_count(row['appointment_date'].date(), row['case_completion_date'].date()) - 1
                days = max(0, days)
                tats.append(days)
            except:
                tats.append(0)
        
        tat_data['closure_tat_val'] = tats
        
        # Bucket
        tat_data['Bucket'] = tat_data['closure_tat_val'].apply(
            lambda x: str(x) if x < 3 else "3+"
        )
        
        
        # Aggregation
        counts = tat_data['Bucket'].value_counts().sort_index()
        # Sort custom: 0, 1, 2, 3+
        order = ['0', '1', '2', '3+']
        counts = counts.reindex(order, fill_value=0)
        
        # Chart
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(
                x=counts.index, 
                y=counts.values,
                text=counts.values,
                title="Closure TAT (Total Cases)",
                labels={'x': 'Days Taken', 'y': 'Number of Cases'},
                color=counts.index,
                color_discrete_map={'0': '#10b981', '1': '#34d399', '2': '#fbbf24', '3+': '#ef4444'}
            )
            fig1.update_layout(
                showlegend=False, 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            st.plotly_chart(fig1, use_container_width=True) 
        
        with col2:
            # Scheduled TAT
            
            tat_data_sched = df.copy() # Start fresh from main filtered df
            # Re-apply status filter (closed cases) or do we want all? Closure TAT tab implies closed cases.
            status_norm_sched = tat_data_sched['case_status'].apply(MISConfig.normalize_status_value)
            tat_data_sched = tat_data_sched[status_norm_sched.isin(norm_closed)] # Closed cases only
            
            tat_data_sched['case_received_date'] = to_dt(tat_data_sched['case_received_date'])
            tat_data_sched['appointment_fixed_date'] = to_dt(tat_data_sched['appointment_fixed_date'])
            tat_data_sched['sched_diff'] = (tat_data_sched['appointment_fixed_date'] - tat_data_sched['case_received_date']).dt.days
            tat_data_sched['sched_diff'] = tat_data_sched['sched_diff'].fillna(0).clip(lower=0).astype(int)
            
            tat_data_sched['SchedBucket'] = tat_data_sched['sched_diff'].apply(
                lambda x: str(x) if x < 3 else "3+"
            )
            
            s_counts = tat_data_sched['SchedBucket'].value_counts().reindex(order, fill_value=0)
            
            fig2 = px.bar(
                x=s_counts.index, 
                y=s_counts.values,
                text=s_counts.values,
                title="Scheduled TAT (Total Cases)",
                labels={'x': 'Days Taken', 'y': 'Number of Cases'},
                color=s_counts.index,
                color_discrete_map={'0': '#10b981', '1': '#34d399', '2': '#fbbf24', '3+': '#ef4444'}
            )
            fig2.update_layout(
                showlegend=False, 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    tab1, tab2 = st.tabs(["Closure TAT Data", "Scheduled TAT Data"])
    with tab1: st.dataframe(closure_df, use_container_width=True)
    with tab2: st.dataframe(schedule_df, use_container_width=True)
    
    # Generate Excel in memory without temp files
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        closure_df.to_excel(writer, index=False, sheet_name='Closure TAT')
        schedule_df.to_excel(writer, index=False, sheet_name='Scheduled TAT')
    
    st.download_button(
        "📥 Download Report",
        data=buffer.getvalue(),
        file_name=f"Closure_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def daily_tab():
    st.markdown("## Daily MIS Report")
    
    with st.expander("ℹ️ How Client Report is Calculated"):
        st.markdown("""
        ### Closure Calculation Logic
        
        **Both metrics use RECEIVED DATE (Case Entry Date), NOT Completion Date:**
        
        1. **Total Received:** 
           - Groups all cases by the month they were **received** (case_entry_date)
           - Shows how many cases came in each month
        
        2. **Total Closed:**
           - Groups only **closed** cases by the month they were **received** (case_entry_date)
           - NOT by completion date
           - Shows how many of the received cases are now closed
        
        3. **Closure %:**
           - Formula: `(Closed / Received) × 100`
           - Since both use received date, Closed can never exceed Received
        
        ---
        
        **Example:**
        - January: Received 100 cases
        - Of those 100 cases, 85 are now closed
        - Closure Rate = 85%
        
        **Note:** This approach prevents showing "more closed than received" in a given month.
        """)
    
    if st.session_state.normalized_data is None: return
    
    date_range, clients = render_filters("daily")
    df = filter_dataframe(st.session_state.normalized_data, date_range, clients)
    
    if df.empty: return
    
    gen = DailyMISGenerator(df)
    reports = gen.generate()
    
    if not reports:
        st.warning("No data generated.")
        return
    
    # Show error if present
    if 'error' in reports:
        st.error(f"Error generating report: {reports['error']}")
        st.info("Check the console/terminal for detailed error logs")
        return
        
    tabs = st.tabs(["Case Status", "Client Report", "Drug Cases", "Non-Drug Cases"])
    
    with tabs[0]: 
        if 'case_status' in reports and not reports['case_status'].empty:
            st.dataframe(reports['case_status'], use_container_width=True)
        else:
            st.info("No case status data available")
            
    with tabs[1]:
        if 'client_merged' in reports:
            if not reports['client_merged'].empty:
                st.dataframe(reports['client_merged'], use_container_width=True)
            else:
                st.warning("Client report is empty - No data found in the last 3 months")
        else:
            st.error("client_merged key not in reports")
            
    with tabs[2]:
        if 'drug' in reports and not reports['drug'].empty:
            st.dataframe(reports['drug'], use_container_width=True)
        else:
            st.info("No drug case data available")
            
    with tabs[3]:
        if 'non_drug' in reports and not reports['non_drug'].empty:
            st.dataframe(reports['non_drug'], use_container_width=True)
        else:
            st.info("No non-drug case data available")
        
    # Generate Excel in memory without temp files
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if 'case_status' in reports and not reports['case_status'].empty:
            df = reports['case_status'].copy()
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(map(str, col)).strip('_') for col in df.columns.values]
            df.to_excel(writer, index=False, sheet_name='Case Status')
            
        if 'client_merged' in reports and not reports['client_merged'].empty:
            df = reports['client_merged'].copy()
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(map(str, col)).strip('_') for col in df.columns.values]
            df.to_excel(writer, index=False, sheet_name='Client Report')
            
        if 'drug' in reports and not reports['drug'].empty:
            df = reports['drug'].copy()
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(map(str, col)).strip('_') for col in df.columns.values]
            df.to_excel(writer, index=False, sheet_name='Drug Cases')
            
        if 'non_drug' in reports and not reports['non_drug'].empty:
            df = reports['non_drug'].copy()
            # Flatten MultiIndex columns if present
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = ['_'.join(map(str, col)).strip('_') for col in df.columns.values]
            df.to_excel(writer, index=False, sheet_name='Non-Drug Cases')
    
    st.download_button(
        "📥 Download Report",
        data=buffer.getvalue(),
        file_name=f"Daily_Report_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():
    # Check if already authenticated
    if st.session_state.get('authenticated', False):
        # User is logged in - show dashboard
        init_state()
        
        # Auto-load API data on first login (only once)
        if (st.session_state.selected_system == 'Welleazy' and 
            st.session_state.normalized_data is None and 
            not st.session_state.get('api_load_attempted', False)):
            
            st.session_state.api_load_attempted = True
            try:
                api_endpoint = os.getenv('WELLEAZY_API_ENDPOINT', 'http://api.welleazy.com/PhysicalMedicalMISReport')
                pipeline = WelleazyMISPipeline(api_endpoint=api_endpoint)
                pipeline._ingest_data()
                pipeline._normalize_data()
                
                st.session_state.pipeline = pipeline
                st.session_state.normalized_data = pipeline.normalized_data
                
                # Initialize global bounds
                df = st.session_state.normalized_data
                st.session_state.global_clients = sorted(df['client_name'].dropna().unique().tolist())
                
                if not pd.api.types.is_datetime64_any_dtype(df['case_received_date']):
                    df['case_received_date'] = pd.to_datetime(df['case_received_date'], errors='coerce')
                
                min_d = df['case_received_date'].min()
                max_d = df['case_received_date'].max()
                
                if pd.isna(min_d) or pd.isna(max_d):
                    st.session_state.global_min_date = datetime.now().date()
                    st.session_state.global_max_date = datetime.now().date()
                else:
                    st.session_state.global_min_date = min_d.date()
                    st.session_state.global_max_date = max_d.date()
                
                # st.success("✓ Data loaded successfully!")
            except Exception as e:
                # Log detailed error for debugging
                import traceback
                error_details = traceback.format_exc()
                print(f"API Auto-load Error: {error_details}")
                st.warning(f"⚠️ Could not auto-load API data. You can load manually from sidebar.")
        
        sidebar()
        
        # Route to appropriate system
        if st.session_state.selected_system == 'Welleazy':
            welleazy_main()
        else:
            veriright_main()
        return
    
    # Show login page
    st.markdown("""
        <div class='login-container'>
            <div class='login-header'>
                <div class='login-title'>MIS Dashboard</div>
                <div class='login-subtitle'>Welleazy & VeriRight Systems</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Login form
    with st.form("login_form"):
        st.markdown("### Login")
        username = st.text_input("Username", placeholder="admin or manager")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            credentials = load_credentials()
            
            if username in credentials:
                user_data = credentials[username]
                if verify_password(password, user_data['password']):
                    # Successful login
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.name = user_data['name']
                    # Don't reset api_load_attempted - preserve data across logins
                    st.success(f"Welcome {user_data['name']}!")
                    st.rerun()
                else:
                    st.error("Incorrect password")
            else:
                st.error("Username not found")
    
    


def welleazy_main():
    """Welleazy MIS Dashboard"""
    st.markdown("# Welleazy MIS")
    st.markdown(f"*Last updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}*")
    # st.markdown("---")
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "Overview",
        "Clients", 
        "Operations",
        "TAT MIS",
        "Pending",
        "Closure TAT",
        "Daily MIS"
    ])
    
    with tab1: overview_tab()
    with tab2: client_tab()
    with tab3: operations_tab()
    with tab4: tat_tab()
    with tab5: pending_tab()
    with tab6: closure_tab()
    with tab7: daily_tab()


def veriright_main():
    """VeriRight MIS Reports Dashboard"""
    st.markdown("## VeriRight MIS Reports")
    
    if st.session_state.vr_normalized_data is None:
        st.info("Please upload VeriRight data files (HDFC Life, SBI Life, Star Union Dai-ichi, etc.) using the sidebar")
        return
    
    # Create tabs for different report types
    tabs = st.tabs([
        "Overall MIS",
        "SUD MIS",
        "SBI MIS", 
        "HDFC Vcheck",
        "HDFC ITR"
    ])
    
    with tabs[0]: veriright_overall_mis_tab()
    with tabs[1]: veriright_sud_tab()
    with tabs[2]: veriright_sbi_tab()
    with tabs[3]: veriright_hdfc_vcheck_tab()
    with tabs[4]: veriright_hdfc_itr_tab()


def veriright_daily_mis_tab():
    """Daily MIS Tab - Consolidated Report"""
    st.markdown("### Daily MIS Report")
    st.caption("Consolidated client-wise monthly performance")
    
    # Filters
    date_range, clients = render_veriright_filters("vr_daily")
    df = filter_veriright_dataframe(st.session_state.vr_normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        st.info("Try adjusting the date range or client filters to see data.")
        return
    
    # Show data info for debugging
    st.info(f"Loaded {len(df)} cases for Daily MIS")
    
    # Generate Daily MIS Report
    gen = VeriRightDailyMISGenerator(df)
    reports = gen.generate()
    
    if not reports:
        st.error("No reports generated. The data might be empty after filtering.")
        return
        
    if 'error' in reports:
        st.error(f"Error generating report: {reports.get('error', 'Unknown error')}")
        return
    
    # --- KPI Section ---
    summary = reports.get('summary', pd.DataFrame())
    if not summary.empty:
        # Extract metrics from the summary dataframe (it has 1 row)
        s_row = summary.iloc[0]
        total = s_row.get('Total Cases', 0)
        closed = s_row.get('Closed Cases', 0)
        rate = s_row.get('Closure Rate', '0%')
        pending = s_row.get('Pending Cases', 0)
        
        # Clean rate string to float for color logic
        try:
            rate_val = float(str(rate).replace('%', ''))
        except:
            rate_val = 0
            
        rate_status = "excellent" if rate_val >= 90 else "warning" if rate_val >= 80 else "critical"
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='metric-label'>Total Cases</div>
                <div class='big-metric'>{total}</div>
                <div class='metric-sub'>Pending: {pending}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='metric-label'>Closed Cases</div>
                <div class='big-metric'>{closed}</div>
                <div class='metric-sub'>Successfully Verified</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col3:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='metric-label'>Closure Rate</div>
                <div class='big-metric status-{rate_status}'>{rate}</div>
                <div class='metric-sub'>Target: 85%</div>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    # --- Charts Section ---
    status_df = reports.get('status_breakdown', pd.DataFrame())
    client_df = reports.get('client_monthly', pd.DataFrame())
    
    if not status_df.empty or not client_df.empty:
        col_charts1, col_charts2 = st.columns([1, 2])
        
        with col_charts1:
            if not status_df.empty:
                st.markdown("### Status Distribution")
                fig_status = px.pie(
                    status_df, 
                    values='Count', 
                    names='Case Status',
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                fig_status.update_layout(
                    height=350,
                    margin=dict(t=0, b=0, l=0, r=0),
                    showlegend=False,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                fig_status.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_status, use_container_width=True)
        
        with col_charts2:
            if not client_df.empty:
                st.markdown("### Client Performance (Volume)")
                # Aggregating by client for the chart in case multiple months exist
                client_chart_data = client_df.groupby('Client name')[['Total case received', 'closed case']].sum().reset_index()
                client_chart_data = client_chart_data.sort_values('Total case received', ascending=False).head(10)
                
                fig_client = px.bar(
                    client_chart_data,
                    x='Client name',
                    y=['Total case received', 'closed case'],
                    barmode='group',
                    title="",
                    labels={'value': 'Cases', 'variable': 'Type', 'Client name': ''},
                    color_discrete_map={'Total case received': '#6366f1', 'closed case': '#10b981'}
                )
                fig_client.update_layout(
                    height=350,
                    margin=dict(t=20, b=20, l=0, r=0),
                    xaxis=dict(showgrid=False),
                    yaxis=dict(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)'),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig_client, use_container_width=True)

    st.markdown("---")

    # Create tabs similar to Welleazy Daily MIS
    tabs = st.tabs(["Case Status Breakdown", "Client Report (Detailed)"])
    
    with tabs[0]:
        # Case Status Breakdown
        if not status_df.empty:
            st.dataframe(
                status_df, 
                use_container_width=True, 
                height=400,
                column_config={
                    "Percentage": st.column_config.ProgressColumn(
                        "Distribution",
                        format="%s",
                        min_value=0,
                        max_value=100,
                    )
                }
            )
        else:
            st.info("No case status data available")
    
    with tabs[1]:
        # Client Monthly Report
        if not client_df.empty:
            # Calculation explanation dropdown
            with st.expander("ℹ️ How These Calculations Work"):
                st.markdown("""
                ### Client Report Calculation Logic
                
                This report follows the **same methodology as Welleazy Daily MIS**:
                
                ---
                
                #### 📊 Core Principle
                **Both "Total case received" and "Closed case" use the SAME date - Case Received Date (NOT Completion Date)**
                
                This ensures that:
                - Closed cases can never exceed received cases in any month
                - We track closure performance for each monthly cohort
                
                ---
                
                #### 1️⃣ Total case received
                **What it shows:** How many cases came in during this month  
                **Source Column:** `Case Rec'd Date` (or `Case Recd Date`)  
                **Logic:**
                ```
                - Filter all cases where Case Rec'd Date falls in the month
                - Count all cases (regardless of current status)
                - Group by Client Name and Month
                ```
                **Example:** If November shows 100, it means 100 cases were received in November
                
                ---
                
                #### 2️⃣ Closed case
                **What it shows:** How many of the received cases are NOW closed  
                **Source Columns:**
                - Date: `Case Rec'd Date` (same as above)
                - Status: `Case status` column
                
                **Logic:**
                ```
                - Take ONLY cases received in that specific month
                - Check their CURRENT status
                - Count cases with status = "Closed - submitted to insurance"
                ```
                
                **Closed Status Values:**
                - `Closed - submitted to insurance` ✓ (Primary)
                - `Vcheck completed – QC Pending` ✓
                - `Closed`, `Case Closed`, `Completed` ✓
                - `Verification Completed`, `Report Submitted` ✓
                
                **Example:** 
                - November: 100 cases received
                - Of those 100, currently 85 are closed
                - Closed case = 85
                
                ---
                
                #### 3️⃣ % As per Close
                **What it shows:** Closure rate for each monthly cohort  
                **Formula:**
                ```
                (Closed case / Total case received) × 100
                ```
                
                **Example:**
                - Total received: 100
                - Closed: 85
                - % As per Close = (85/100) × 100 = 85.0%
                
                **Color Coding:**
                - 🟢 **Green** ≥ 90% - Excellent performance
                - 🟡 **Yellow** 80-89% - Good performance
                - 🔴 **Red** < 80% - Needs attention
                
                ---
                
                ### 🔍 Key Points
                
                1. **Same Date for Both Metrics:**
                   - Both use `Case Rec'd Date` 
                   - NOT using completion date for closed cases
                
                2. **Current Status Check:**
                   - Closed count reflects the CURRENT state
                   - Cases may be received in November but closed in December
                
                3. **Cohort Analysis:**
                   - Each month represents a cohort of cases
                   - We track how well that cohort performs over time
                
                4. **No Over-counting:**
                   - Since both use received date, closed ≤ received always
                
                ---
                
                ### 📁 Column Mapping by Client
                
                **HDFC Life:**
                - Completion tracking: `KYC Completion Date`
                
                **SBI Life:**  
                - Completion tracking: `Case Completetion Date` (note spelling)
                
                **Star Union Dai-ichi (SUD):**
                - Completion tracking: `MER Completion Date`
                
                ---
                
                ### ❌ Excluded Cases
                
                **Cancelled cases are filtered out:**
                - `Cancelled by Insurance Company`
                - `Cancelled by insurance company` 
                - `Cancelled by insurance Company`
                - `Cancelled`, `Cancelled Cases`, `Cancel`
                
                These are removed during data processing and don't appear in any counts.
                """)
            
            # Use column config for cleaner display
            st.dataframe(
                client_df, 
                use_container_width=True, 
                height=500,
                column_config={
                    "% As per Close": st.column_config.ProgressColumn(
                        "Closure Rate",
                        format="%s",
                        min_value=0,
                        max_value=100
                    ),
                    "Targets": st.column_config.TextColumn("Targets")
                }
            )
        else:
            st.warning("No client report data available")
    
    # Download Report
    st.markdown("---")
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if 'status_breakdown' in reports and not reports['status_breakdown'].empty:
            reports['status_breakdown'].to_excel(writer, sheet_name='Case Status', index=False)
        if 'client_monthly' in reports and not reports['client_monthly'].empty:
            reports['client_monthly'].to_excel(writer, sheet_name='Client Report', index=False)
            
        # Also include summary
        if 'summary' in reports and not reports['summary'].empty:
            reports['summary'].to_excel(writer, sheet_name='Summary', index=False)
    
    st.download_button(
        "📥 Download Daily MIS Report",
        data=buffer.getvalue(),
        file_name=f"VeriRight_Daily_MIS_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def veriright_sud_tab():
    """SUD MIS Tab - Star Union Dai-ichi Life Insurance"""
    st.markdown("### SUD MIS - Star Union Dai-ichi Life Insurance")
    st.caption("Daily Morning Report (MON-SAT)")
    
    with st.expander("📊 Detailed Calculation Methodology", expanded=False):
        st.markdown("""
        ### SUD MIS Calculation Details
        
        #### 📋 Data Source & Filtering:
        ```
        Filter Criteria:
        - Client name contains "Star Union" (case-insensitive)
        - Includes: Star Union Dai-ichi Life Ins, Star Union Dai-ichi Life Insurance
        - Uses date range from user filter (default: all data)
        ```
        
        ---
        
        #### 🔢 Calculation Method:
        ```
        Step 1: Filter data for Star Union clients
        Step 2: Group all cases by Case Status
        Step 3: Count frequency of each status using value_counts()
        Step 4: Add Grand Total row = SUM of all status counts
        
        Example:
        If we have:
        - Closed: 250 cases
        - In Progress: 80 cases
        - Pending: 45 cases
        → Grand Total = 375 cases
        ```
        
        ---
        
        #### 📊 Column Mapping:
        **Source → Normalized:**
        - `MER Completion Date` → `case_completion_date`
        - `Case Rec'd Date` → `case_received_date`
        - `Case Status` → `case_status`
        
        ---
        
        #### 📈 Output Format:
        Simple 2-column pivot table:
        
        | Case Status | Count |
        |------------|-------|
        | Closed | 250 |
        | In Progress | 80 |
        | Pending | 45 |
        | **Grand Total** | **375** |
        
        ---
        
        #### ⏰ Report Frequency:
        **Daily Morning Report (MON-SAT)**
        - Generated every morning for previous day's data
        - Shows cumulative status distribution
        """)
    
    # Add filters
    date_range, clients = render_veriright_filters("vr_sud")
    df = filter_veriright_dataframe(st.session_state.vr_normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Generate SUD Report
    gen = SUDReportGenerator(df)
    pivot = gen.generate()
    
    if pivot.empty:
        st.warning("No SUD data found. Please upload Star Union Dai-ichi Life Insurance data.")
        return
    
    st.markdown("#### Case Status Pivot Table")
    st.dataframe(pivot, use_container_width=True, height=400)
    
    # Download button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pivot.to_excel(writer, sheet_name='SUD MIS', index=False)
    
    st.download_button(
        "📥 Download SUD MIS",
        data=buffer.getvalue(),
        file_name=f"SUD_MIS_{datetime.now().strftime('%d_%B')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def veriright_sbi_tab():
    """SBI MIS Tab - SBI Life"""
    st.markdown("### SBI MIS - SBI Life")
    st.caption("Daily Morning Report (MON-FRI) - Video KYC from Jan 2025")
    
    with st.expander("📊 Detailed Calculation Methodology", expanded=False):
        st.markdown("""
        ### SBI MIS Calculation Details
        
        #### 📋 Data Source & Filtering:
        ```
        Dual Filter Criteria (Both must be TRUE):
        1. Client name contains "SBI" (case-insensitive)
        2. Activity Type contains "Video KYC" OR "VKYC"
        
        Valid Activity Types:
        - Video KYC
        - VKYC
        - Video KYC Verification
        
        Date Range: Uses user-selected filter (default: all data)
        ```
        
        ---
        
        #### 🔢 Calculation Method:
        ```
        Step 1: Filter data where (Client = SBI) AND (Activity = Video KYC)
        Step 2: Group filtered cases by Case Status
        Step 3: Count frequency of each status
        Step 4: Add Total row = SUM of all status counts
        
        Example:
        From 1,000 SBI cases:
        - 850 are Video KYC → Selected for report
        - 150 are other activity types → Excluded
        
        Status Distribution:
        - Completed: 600
        - In Progress: 150
        - Pending: 100
        → Total = 850 Video KYC cases
        ```
        
        ---
        
        #### 📊 Column Mapping:
        **Source → Normalized:**
        - `Case Completetion Date` → `case_completion_date` (note: typo in source)
        - `Case Rec'd Date` → `case_received_date`
        - `Case Status` → `case_status`
        - `Activity Type` → `activity_type`
        
        ---
        
        #### 📈 Output Format:
        
        | Case Status | Count |
        |------------|-------|
        | Completed | 600 |
        | In Progress | 150 |
        | Pending | 100 |
        | **Total** | **850** |
        
        ---
        
        #### ⏰ Report Frequency:
        **Daily Morning Report (MON-FRI) - Video KYC from Jan 2025**
        
        ---
        
        #### ⚠️ Known Limitations:
        - **LOT** and **Completed Via** fields require external SBI Status file
        - These fields not yet integrated (planned enhancement)
        - Current report shows status distribution only
        """)
    
    # Add filters
    date_range, clients = render_veriright_filters("vr_sbi")
    df = filter_veriright_dataframe(st.session_state.vr_normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Generate SBI Report
    gen = SBIReportGenerator(df)
    reports = gen.generate()
    
    if not reports or 'status_pivot' not in reports:
        st.warning("No SBI Life Video KYC data found. Please upload SBI Life data with Activity Type = Video KYC.")
        return
    
    st.markdown("#### Case Status Pivot")
    st.dataframe(reports['status_pivot'], use_container_width=True, height=400)
    
    if 'note' in reports:
        st.info(f"ℹ️ {reports['note']}")
    
    # Download button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        reports['status_pivot'].to_excel(writer, sheet_name='SBI Status Pivot', index=False)
    
    st.download_button(
        "📥 Download SBI MIS",
        data=buffer.getvalue(),
        file_name=f"Overall_SBI_MIS_{datetime.now().strftime('%d_%B')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def veriright_hdfc_vcheck_tab():
    """HDFC Vcheck Tab"""
    st.markdown("### HDFC Vcheck MIS - HDFC Life")
    st.caption("Daily EOD Report (MON-SAT) - VKYC IC Format from April")
    
    with st.expander("📊 Detailed Calculation Methodology", expanded=False):
        st.markdown("""
        ### HDFC Vcheck MIS Calculation Details
        
        #### 📋 Data Source & Auto-Classification:
        ```
        Classification Rule (applied during normalization):
        IF Case Type = "Video check" 
           AND Branch ≠ "Manual"
        → Client name = "HDFC Life Vcheck"
        
        Exclusions:
        - Manual branch cases (classified as "HDFC ITR manual")
        - Non-video check cases (classified as "HDFC Auto" or "HDFC ITR manual")
        
        Date Range: Uses user-selected filter
        ```
        
        ---
        
        #### 🔢 Calculation Method:
        ```
        Step 1: Filter cases where client_name = "HDFC Life Vcheck"
        Step 2: Extract month from Case Rec'd Date (format: Jan, Feb, Mar)
        Step 3: Create crosstab matrix:
                - Rows: Case Status values
                - Columns: Month names
                - Cells: COUNT of cases
        Step 4: Add Total column = SUM across all months for each status
        
        Example Matrix:
        
        Case Status    | Oct | Nov | Dec | Total
        ---------------|-----|-----|-----|------
        Completed      | 150 | 180 | 165 | 495
        In Progress    |  30 |  25 |  40 |  95
        Pending        |  20 |  15 |  18 |  53
        ```
        
        ---
        
        #### 📊 Column Mapping:
        **Source → Normalized:**
        - `KYC Completion Date` → `case_completion_date`
        - `Case Rec'd Date` → `case_received_date`
        - `Case Status` → `case_status`
        - `Case Type` → Used for classification logic
        - `Branch` → Used to exclude Manual cases
        
        ---
        
        #### 📈 Output Format:
        **Crosstab Matrix:** Status Distribution Across Months
        
        - **Rows:** All unique case statuses found in data
        - **Columns:** Months from date range (chronologically sorted)
        - **Total Column:** Sum of each status across all months
        - **Values:** Count of cases matching status + month combination
        
        ---
        
        #### 🎯 Use Case:
        Track VKYC (Video KYC) case status progression month-over-month
        - Identify which statuses accumulate over time
        - Monitor completion rates by month
        - Spot bottlenecks in specific months
        
        ---
        
        #### ⏰ Report Frequency:
        **Daily EOD Report (MON-SAT) - VKYC IC Format from April**
        """)
    
    # Add filters
    date_range, clients = render_veriright_filters("vr_hdfc_vcheck")
    df = filter_veriright_dataframe(st.session_state.vr_normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Generate HDFC Vcheck Report
    gen = HDFCVcheckReportGenerator(df)
    pivot = gen.generate()
    
    if pivot.empty:
        st.warning("No HDFC Life VKYC data found. Please upload HDFC Life data with Activity Type = VKYC.")
        return
    
    st.markdown("#### Case Status by Month")
    st.dataframe(pivot, use_container_width=True, height=400)
    
    # Download button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        pivot.to_excel(writer, sheet_name='HDFC VKYC IC')
    
    st.download_button(
        "📥 Download HDFC Vcheck MIS",
        data=buffer.getvalue(),
        file_name=f"HDFC_VKYC_IC_{datetime.now().strftime('%d_%B')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def veriright_hdfc_itr_tab():
    """HDFC ITR Tab"""
    st.markdown("### HDFC ITR MIS - HDFC ITR Manual")
    st.caption("MON-SAT Report - VMS Format from April")
    
    with st.expander("📊 Detailed Calculation Methodology", expanded=False):
        st.markdown("""
        ### HDFC ITR MIS Calculation Details
        
        #### 📋 Data Source & Auto-Classification:
        ```
        Classification Logic (applied during normalization):
        
        A. HDFC ITR manual (Assisted):
           IF Branch = "Manual" AND Case Type ≠ "Video check"
           → Client name = "HDFC ITR manual"
        
        B. HDFC Auto (Non-Assisted):
           IF Branch = "Non Assisted" AND Case Type ≠ "Video check"
           → Client name = "HDFC Auto"
        
        Exclusions:
        - Video check cases (classified as "HDFC Life Vcheck")
        - Cases without Branch information
        
        Date Range: Uses user-selected filter
        ```
        
        ---
        
        #### 🔢 Calculation Method:
        ```
        Step 1: Split data into two groups:
                Group A: HDFC ITR manual (Branch = "Manual")
                Group B: HDFC Auto (Branch = "Non Assisted")
        
        Step 2: CRITICAL - Remove duplicates:
                - Use Application Number as deduplication key
                - Keep first occurrence, drop subsequent duplicates
                - This prevents double-counting same application
        
        Step 3: For each group separately:
                - Group by Case Status
                - Count frequency using value_counts()
                - Add Total row = SUM of all status counts
        
        Example:
        HDFC ITR manual (Assisted):
        - Raw records: 520
        - After deduplication: 500 unique applications
        - Status breakdown:
          • Completed: 350
          • In Progress: 100
          • Pending: 50
        → Total = 500
        
        HDFC Auto (Non-Assisted):
        - Raw records: 1,080
        - After deduplication: 1,000 unique applications
        - Status breakdown:
          • Completed: 800
          • In Progress: 120
          • Pending: 80
        → Total = 1,000
        ```
        
        ---
        
        #### 🔑 Why Deduplication?
        ```
        Problem: Same application may appear multiple times due to:
        - Multiple status updates
        - Re-submissions
        - Data extraction at different times
        
        Solution: Keep only first occurrence per Application Number
        - Ensures accurate case count
        - Prevents inflated metrics
        - Maintains data integrity
        ```
        
        ---
        
        #### 📊 Column Mapping:
        **Source → Normalized:**
        - `KYC Completion Date` → `case_completion_date`
        - `Case Rec'd Date` → `case_received_date`
        - `Case Status` → `case_status`
        - `Branch` → Used for Assisted/Non-Assisted classification
        - `Application Number` → Deduplication key (CRITICAL)
        - `Case Type` → Used to exclude Video check
        
        ---
        
        #### 📈 Output Format:
        **Two Side-by-Side Tables:**
        
        **Left: HDFC ITR manual (Assisted)**
        | Case Status | Count |
        |------------|-------|
        | Completed | 350 |
        | In Progress | 100 |
        | Pending | 50 |
        | **Total** | **500** |
        
        **Right: HDFC Auto (Non-Assisted)**
        | Case Status | Count |
        |------------|-------|
        | Completed | 800 |
        | In Progress | 120 |
        | Pending | 80 |
        | **Total** | **1,000** |
        
        ---
        
        #### 🎯 Use Case:
        Compare performance between:
        - **Assisted** (Manual branch): Higher touch, manual processing
        - **Non-Assisted** (Auto): Automated processing, self-service
        
        Key Metrics:
        - Completion rates per channel
        - Pending case distribution
        - Volume comparison
        
        ---
        
        #### ⏰ Report Frequency:
        **MON-SAT Report - VMS Format from April**
        """)
    
    # Add filters
    date_range, clients = render_veriright_filters("vr_hdfc_itr")
    df = filter_veriright_dataframe(st.session_state.vr_normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Generate HDFC ITR Report
    gen = HDFCITRReportGenerator(df)
    reports = gen.generate()
    
    if not reports or ('assisted' not in reports and 'non_assisted' not in reports):
        st.warning("No HDFC ITR data found. Please upload HDFC ITR data.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### HDFC ITR manual (Assisted)")
        if 'assisted' in reports and not reports['assisted'].empty:
            st.dataframe(reports['assisted'], use_container_width=True, height=400)
        else:
            st.info("No HDFC ITR manual cases found")
    
    with col2:
        st.markdown("#### HDFC Auto (Non-Assisted)")
        if 'non_assisted' in reports and not reports['non_assisted'].empty:
            st.dataframe(reports['non_assisted'], use_container_width=True, height=400)
        else:
            st.info("No HDFC Auto cases found")
    
    # Status Normalization Info
    st.info("""
    ℹ️ **Status Cleanup Applied:** Error messages like "no data found", "error", "doc not reflecting" 
    have been automatically categorized as **"Technical Error - Data Issue"** for clearer reporting. 
    Customer-related issues are marked as **"Pending - Customer Action Required"**.
    """)
    
    # Download button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if 'assisted' in reports and not reports['assisted'].empty:
            reports['assisted'].to_excel(writer, sheet_name='Assisted', index=False)
        if 'non_assisted' in reports and not reports['non_assisted'].empty:
            reports['non_assisted'].to_excel(writer, sheet_name='Non-Assisted', index=False)
        if 'all_data' in reports and not reports['all_data'].empty:
            reports['all_data'].to_excel(writer, sheet_name='All Data', index=False)
    
    st.download_button(
        "📥 Download HDFC ITR MIS",
        data=buffer.getvalue(),
        file_name=f"Copy_of_veriright_ITR_MIS_{datetime.now().strftime('%B_%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def veriright_overall_mis_tab():
    """Overall MIS Tab - Consolidated EOD Report"""
    st.markdown("### Overall VeriRight MIS")
    st.caption("End of Day Report (MON-FRI) - Consolidated View")
    
    with st.expander("📊 Detailed Calculation Methodology", expanded=False):
        st.markdown("""
        ### Overall MIS Calculation Details
        
        #### 1️⃣ **Total Case Received**
        ```
        Formula: COUNT(All cases where Case Received Date falls in the specific month)
        
        Logic:
        - Extract month from "Case Rec'd Date" column
        - Group cases by Client Name and Month
        - Count total records for each group
        
        Example:
        If HDFC Life has 1,956 cases received in October 2023
        → Total case received = 1,956
        ```
        
        ---
        
        #### 2️⃣ **Closed Case** (Dual Logic)
        ```
        Formula: COUNT(Cases that are either status-closed OR have completion date)
        
        Dual Logic (OR condition):
        A. Status-based closure: Case Status ∈ ['Closed', 'Completed', 'Verification Completed']
           OR
        B. Completion-based closure: Case Completion Date is NOT NULL (exists)
        
        A case is considered CLOSED if EITHER condition A OR condition B is TRUE.
        
        Example:
        From 1,956 cases received in October:
        - 1,200 have status = "Closed"
        - 195 have completion date filled but status = "In Progress"
        → Closed case = 1,395 (both groups combined)
        ```
        
        **Why Dual Logic?**
        - Some cases may have completion dates but status not updated
        - Some cases may have status updated but completion date pending
        - This ensures accurate closure counting
        
        ---
        
        #### 3️⃣ **% As per Close (Closure Percentage)**
        ```
        Formula: (Closed case / Total case received) × 100
        
        Calculation:
        - Uses the "Closed case" count (with dual logic)
        - Divided by "Total case received"
        - Rounded to 1 decimal place
        
        Example:
        Closed case = 1,395
        Total case received = 1,956
        → % As per Close = (1,395 / 1,956) × 100 = 71.3%
        ```
        
        **Color Coding:**
        - 🟢 **Green**: ≥ 90% (Excellent performance)
        - 🟡 **Yellow**: 80-89% (Good performance)  
        - 🔴 **Red**: < 80% (Needs attention)
        
        ---
        
        #### 4️⃣ **Closure Date Case**
        ```
        Formula: COUNT(Cases where Completion Date falls in the specific month)
        
        Logic:
        - Filter cases by Case Completion Date (not Case Received Date)
        - Extract month from "Case Completion Date"
        - Count cases completed in that specific month
        - Includes cases received in ANY month (not just current month)
        
        Example:
        Cases completed in October (regardless of when received):
        - 500 cases received in Sept and completed in Oct
        - 972 cases received in Oct and completed in Oct
        → Closure Date case = 1,472
        ```
        
        **Key Difference:**
        - **Closed Case**: Cases received in Month X and marked closed
        - **Closure Date Case**: Cases actually completed in Month X (any receive date)
        
        ---
        
        #### 5️⃣ **Targets**
        ```
        Formula: Predefined constant per client
        
        Logic:
        - Retrieved from CLIENT_TARGETS configuration
        - Set manually based on business requirements
        - Does NOT auto-calculate
        
        Example Configuration:
        • HDFC Life Vcheck: 2,300
        • SBI Life: 1,000
        • Star Union Dai-ichi Life Ins: 200
        ```
        
        ---
        
        ### 📈 Complete Calculation Flow:
        
        **Step 1:** Data Loading & Merging → Multiple Excel/CSV files combined
        
        **Step 2:** Column Normalization → Map variant column names to standard format
        
        **Step 3:** Date Parsing → Convert to datetime, extract month/year
        
        **Step 4:** Status Categorization → Classify as Closed/Pending/Cancelled
        
        **Step 5:** Monthly Grouping → For each Client + Month combination, calculate metrics
        
        **Step 6:** Report Generation → Create DataFrame, sort, format, apply color coding
        
        ---
        
        ### 💡 Example Walkthrough:
        
        **Sample: HDFC Life - October 2023**
        
        | Metric | Value | Calculation |
        |--------|-------|-------------|
        | Total case received | 1,956 | Cases with receive date in Oct |
        | Closed case | 1,395 | 1,200 (status) + 195 (completion) |
        | % As per Close | 71.3% 🔴 | (1,395 ÷ 1,956) × 100 |
        | Closure Date case | 1,472 | Completion date in Oct |
        | Targets | 2,300 | From config |
        
        **Performance Interpretation:**
        - Closure rate of 71.3% is below 80% → **Red alert**
        - Gap to target: 2,300 - 1,956 = 344 cases short
        - Higher closure date count (1,472 vs 1,395) suggests backlog clearance
        
        ---
        
        ### 🎯 Status Pivot & Client Pivots:
        - **Status Pivot:** Crosstab of case_status × Month (shows distribution)
        - **Client Pivots:** Individual client status breakdowns by month
        - **Visualizations:** Monthly trends (Received vs Closed), Volume by Client
        """)
    
    # Add filters
    date_range, clients = render_veriright_filters("vr_overall")
    df = filter_veriright_dataframe(st.session_state.vr_normalized_data, date_range, clients)
    
    if df.empty:
        st.warning("No data available for the selected filters.")
        return
    
    # Generate Overall MIS Report
    gen = OverallMISReportGenerator(df)
    reports = gen.generate()
    
    if not reports or 'client_summary' not in reports:
        st.warning("No data available for Overall MIS.")
        return
    
    # Client Summary Table
    st.markdown("#### Client Performance Summary")
    if 'client_summary' in reports and not reports['client_summary'].empty:
        summary_df = reports['client_summary']
        
        # --- KPI Section ---
        total_received = summary_df['Total case received'].sum()
        total_closed = summary_df['Closed case'].sum()
        overall_rate = (total_closed / total_received * 100) if total_received > 0 else 0
        rate_status = "excellent" if overall_rate >= 90 else "warning" if overall_rate >= 80 else "critical"
        
        col1, col2, col3 = st.columns(3)
        with col1:
             st.markdown(f"""
            <div class='kpi-card'>
                <div class='metric-label'>Total Received</div>
                <div class='big-metric'>{total_received:,}</div>
                <div class='metric-sub'>Selected Period</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
             st.markdown(f"""
            <div class='kpi-card'>
                <div class='metric-label'>Total Closed</div>
                <div class='big-metric'>{total_closed:,}</div>
                <div class='metric-sub'>Processed</div>
            </div>
            """, unsafe_allow_html=True)
        with col3:
             st.markdown(f"""
            <div class='kpi-card'>
                <div class='metric-label'>Overall Closure Rate</div>
                <div class='big-metric status-{rate_status}'>{overall_rate:.1f}%</div>
                <div class='metric-sub'>Target: 85%</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # --- Charts ---
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            # Monthly Trend
            monthly_trend = summary_df.groupby('Month')[['Total case received', 'Closed case']].sum().reset_index()
            # Sort by month? summary_df might already be sorted by date or we need logic. 
            # Month is string 'Jan', 'Feb'. Logic in generator sorted by date. Trust generator order if preserved?
            # Groupby might mess up order. Let's use Month_Sort if available in raw data, but summary_df doesn't have it.
            # Generator: report_df includes 'Month'. 
            # Simple aggregation:
            fig_trend = px.bar(
                monthly_trend, 
                x='Month', 
                y=['Total case received', 'Closed case'],
                barmode='group',
                title='Monthly Volume Trends',
                color_discrete_map={'Total case received': '#6366f1', 'Closed case': '#10b981'}
            )
            fig_trend.update_layout(
                height=350, 
                plot_bgcolor='rgba(0,0,0,0)', 
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.2)')
            )
            st.plotly_chart(fig_trend, use_container_width=True)
            
        with col_c2:
             # Client Volume Share
             client_vol = summary_df.groupby('Client name')['Total case received'].sum().reset_index()
             client_vol = client_vol.sort_values('Total case received', ascending=False).head(8)
             fig_vol = px.pie(
                 client_vol, 
                 values='Total case received', 
                 names='Client name', 
                 title='Volume by Client',
                 hole=0.4,
                 color_discrete_sequence=px.colors.qualitative.Prism
             )
             fig_vol.update_layout(
                 height=350,
                 plot_bgcolor='rgba(0,0,0,0)',
                 paper_bgcolor='rgba(0,0,0,0)'
             )
             st.plotly_chart(fig_vol, use_container_width=True)

        
        # Apply conditional formatting
        def highlight_closure(val):
            if isinstance(val, str) and '%' in val:
                try:
                    pct = int(val.replace('%', ''))
                    if pct >= 90:
                        return 'background-color: #d1fae5; color: #065f46'
                    elif pct >= 80:
                        return 'background-color: #fef3c7; color: #92400e'
                    else:
                        return 'background-color: #fee2e2; color: #991b1b'
                except:
                    pass
            return ''
        
        styled_df = summary_df.style.map(highlight_closure, subset=['% As per Close'])
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            height=400
        )
    
    st.markdown("---")
    
    # Status Pivot
    st.markdown("#### Case Status Distribution by Month")
    if 'status_pivot' in reports:
        st.dataframe(reports['status_pivot'], use_container_width=True, height=300)
    
    # Download button
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        if 'client_summary' in reports and not reports['client_summary'].empty:
            reports['client_summary'].to_excel(writer, sheet_name='Client Summary', index=False)
        if 'status_pivot' in reports:
            reports['status_pivot'].to_excel(writer, sheet_name='Status Pivot')
    
    st.download_button(
        "📥 Download Overall MIS",
        data=buffer.getvalue(),
        file_name=f"Overall_VeriRight_MIS_{datetime.now().strftime('%Y%m%d')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    main()
