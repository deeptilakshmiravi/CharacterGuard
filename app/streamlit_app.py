import streamlit as st
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="CharacterGuard Dashboard", layout="wide", page_icon="🛡️")

# 2. Header Section
st.title("🛡️ CharacterGuard: Security & QA Dashboard")
st.write("Automated Adversarial Testing Results")
st.divider()

# 3. Load the Data Contract using the new file path
try:
    # Build the path: Start in 'app', go up one level ('..'), then into 'data/reports'
    file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'reports', 'final_score.json')
    
    with open(file_path, "r") as f:
        data = json.load(f)
        
    st.header(f"Target Character: **{data['character_name']}**")
    st.write("") # Just a little spacing

    # 4. Top-Level Metrics
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Overall Safety Score", f"{data['overall_score']}/100")
    col2.metric("Total Tests Run", data['total_tests'])
    col3.metric("Passed ✅", data['passed'])
    col4.metric("Failed ❌", data['failed'])

    st.divider()

    # 5. Category Breakdown
    st.subheader("Category Performance")
    col_cat1, col_cat2, col_cat3 = st.columns(3)

    scores = data['category_scores']
    col_cat1.metric("Prompt Injection", f"{scores['prompt_injection']}/100")
    col_cat2.metric("Persona Drift", f"{scores['persona_drift']}/100")
    col_cat3.metric("Compliance Breakdown", f"{scores['compliance_tests']}/100")

except FileNotFoundError:
    st.error("⚠️ final_score.json not found. Please make sure the backend saved it in data/reports/")