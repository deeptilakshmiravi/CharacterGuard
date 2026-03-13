import streamlit as st
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="CharacterGuard | Dashboard", layout="wide", page_icon="🛡️")

# 2. Ultimate Dark CSS (Unified Styling)
st.markdown("""
    <style>
    /* Hide the white top bar and set background */
    header, .stApp { 
        background-color: #0f172a !important; 
    }
    
    /* Force ALL text to White */
    h1, h2, h3, p, span, div, label { 
        color: #ffffff !important; 
    }

    /* Metrics Card Styling */
    [data-testid="stMetric"] {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Metric Value specifically (Brighter Blue for contrast) */
    [data-testid="stMetricValue"] {
        color: #38bdf8 !important; 
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #020617 !important;
    }
    
    /* Fix Divider Color */
    hr {
        border-color: #334155 !important;
    }

    /* Fix sidebar navigation text specifically */
    [data-testid="stSidebarNav"] span {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Header
st.title("🛡️ CharacterGuard")
st.write("### Security & QA Dashboard")
st.divider()

# 4. Load Data
try:
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reports', 'final_score.json')
    with open(file_path, "r") as f:
        data = json.load(f)

    st.write(f"### Target Character: **{data['character_name']}**")
    st.write("")

    # 5. Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Safety Score", f"{data['overall_score']}%")
    m2.metric("Total Tests", data['total_tests'])
    m3.metric("Passed ✅", data['passed'])
    m4.metric("Failed ❌", data['failed'])

    st.divider()

    # 6. Category Breakdown
    st.write("### Vulnerability Breakdown")
    c1, c2, c3 = st.columns(3)
    scores = data['category_scores']
    
    with c1:
        st.write("**Prompt Injection**")
        st.progress(scores['prompt_injection'] / 100)
        st.write(f"Score: {scores['prompt_injection']}/100")

    with c2:
        st.write("**Persona Drift**")
        st.progress(scores['persona_drift'] / 100)
        st.write(f"Score: {scores['persona_drift']}/100")

    with c3:
        st.write("**Compliance**")
        st.progress(scores['compliance_tests'] / 100)
        st.write(f"Score: {scores['compliance_tests']}/100")

except FileNotFoundError:
    st.error("⚠️ Data file not found. Check /data/reports/final_score.json")