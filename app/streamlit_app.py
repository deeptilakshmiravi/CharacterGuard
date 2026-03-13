import streamlit as st
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="CharacterGuard | Security Dashboard", layout="wide", page_icon="🛡️")

# 2. Custom CSS for better proportions and "Pop"
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; border: 1px solid #e0e0e0; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stSidebarNavItems"] { font-weight: 600; font-size: 1.1rem; color: white !important; }
    h1 { font-size: 2.5rem !important; font-weight: 800 !important; color: #0f172a; }
    </style>
    """, unsafe_allow_stdio=False)

# 3. Header
st.title("🛡️ CharacterGuard")
st.caption("AI Adversarial Testing Framework | Security & QA Dashboard")
st.divider()

# 4. Load Data
try:
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reports', 'final_score.json')
    with open(file_path, "r") as f:
        data = json.load(f)

    # Use a container for better alignment
    with st.container():
        st.subheader(f"Session Report: {data['character_name']}")
        
        # Row 1: Main KPIs
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Safety Score", f"{data['overall_score']}%", delta="High Risk" if data['overall_score'] < 70 else "Secure")
        m2.metric("Tests Executed", data['total_tests'])
        m3.metric("Passed", data['passed'], delta_color="normal")
        m4.metric("Failures", data['failed'], delta=f"-{data['failed']}", delta_color="inverse")

    st.write("")
    st.write("")

    # Row 2: Category Breakdown with Visual Progress Bars
    st.subheader("Vulnerability Assessment")
    c1, c2, c3 = st.columns(3)
    
    scores = data['category_scores']
    
    with c1:
        st.write("**Prompt Injection**")
        st.progress(scores['prompt_injection'] / 100)
        st.info(f"Score: {scores['prompt_injection']}/100")

    with c2:
        st.write("**Persona Drift**")
        st.progress(scores['persona_drift'] / 100)
        st.success(f"Score: {scores['persona_drift']}/100")

    with c3:
        st.write("**Compliance**")
        st.progress(scores['compliance_tests'] / 100)
        st.warning(f"Score: {scores['compliance_tests']}/100")

except FileNotFoundError:
    st.error("⚠️ Data contract missing. Ensure backend has generated 'final_score.json'.")