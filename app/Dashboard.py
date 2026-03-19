import streamlit as st
import json
import os
import pandas as pd
import requests

# 1. Page Configuration
st.set_page_config(page_title="CharacterGuard | Dashboard", layout="wide", page_icon="🛡️")

# 2. Ultimate Dark CSS (Unified Styling)
st.markdown("""
    <style>
    header, .stApp { background-color: #0f172a !important; }
    h1, h2, h3, p, span, div, label { color: #ffffff !important; }
    [data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding: 20px !important;
        border-radius: 12px !important;
    }
    [data-testid="stMetricValue"] { color: #38bdf8 !important; }
    [data-testid="stSidebar"] { background-color: #020617 !important; }
    hr { border-color: #334155 !important; }
    [data-testid="stSidebarNav"] span { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Sidebar - API Health Check (Member 1 Integration)
with st.sidebar:
    st.write("### 🔌 System Status")
    try:
        # Calling Member 1's Render URL
        res = requests.get("https://charactergaurd-1.onrender.com/health", timeout=3)
        if res.status_code == 200:
            st.success("Backend: ONLINE")
        else:
            st.warning("Backend: WAKING UP")
    except:
        st.error("Backend: OFFLINE")

# 4. Data Loading Logic (Member 6 Integration)
# Loading the mock_config.json provided by Member 6
config_path = os.path.join(os.path.dirname(__file__), '..', 'mock_config.json')
char_config = None
try:
    with open(config_path, 'r') as f:
        char_config = json.load(f)
except:
    pass

# Loading the final scores
report_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reports', 'final_score.json')
try:
    with open(report_path, "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = None

# 5. UI Header
st.title("🛡️ CharacterGuard")
st.write("### Security & QA Dashboard")
st.divider()

if data:
    st.write(f"### Target Character: **{data['character_name']}**")
    
    # Display System Prompt from Member 6's config
    if char_config:
        with st.expander("📝 View Target Character System Prompt"):
            st.code(char_config.get('system_prompt', 'No prompt defined'), language='text')

    # 6. Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Safety Score", f"{data['overall_score']}%")
    m2.metric("Total Tests", data['total_tests'])
    m3.metric("Passed ✅", data['passed'])
    m4.metric("Failed ❌", data['failed'])

    st.divider()

    # 7. Vulnerability Breakdown
    st.write("### Vulnerability Breakdown")
    c1, c2, c3 = st.columns(3)
    scores = data['category_scores']
    
    with c1:
        st.write("**Prompt Injection**")
        st.progress(scores['prompt_injection'] / 100)
    with c2:
        st.write("**Persona Drift**")
        st.progress(scores['persona_drift'] / 100)
    with c3:
        st.write("**Compliance**")
        st.progress(scores['compliance_tests'] / 100)

    st.divider()

    # 8. Detailed Failure Table (Member 6 CSV Integration)
    st.write("### 📜 Detailed Test Log (Raw Runs)")
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw_runs', 'run_001.csv')
    
    try:
        df = pd.read_csv(csv_path)
        # Displaying the table with a clean dark theme look
        st.dataframe(df, use_container_width=True, hide_index=True)
    except Exception:
        st.info("No raw run CSV data found yet.")

else:
    st.error("⚠️ Waiting for report data...")