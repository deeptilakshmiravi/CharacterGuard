import streamlit as st
import json

# 1. Page Configuration
st.set_page_config(page_title="CharacterGuard Dashboard", layout="wide", page_icon="🛡️")

# 2. Header Section
st.title("🛡️ CharacterGuard: Security & QA Dashboard")
st.write("Automated Adversarial Testing Results")
st.divider()

# 3. Load the Data Contract
try:
    with open("final_score.json", "r") as f:
        data = json.load(f)
        
    st.header(f"Target Character: **{data['character_name']}**")
    st.write("") 
    
    # 4. Top-Level Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Overall Safety Score", f"{data['overall_score']}/100")
    col2.metric("Total Tests Run", data['total_tests'])
    col3.metric("Passes ✅", data['passes'])
    col4.metric("Fails ❌", data['fails'])
    
    st.divider()
    
    # 5. Category Breakdown
    st.subheader("Category Performance")
    cat_col1, cat_col2, cat_col3 = st.columns(3)
    
    scores = data['category_scores']
    cat_col1.metric("Prompt Injection", f"{scores['prompt_injection']}/100")
    cat_col2.metric("Persona Drift", f"{scores['persona_drift']}/100")
    cat_col3.metric("Compliance Boundaries", f"{scores['compliance_tests']}/100")

except FileNotFoundError:
    st.error("⚠️ 'final_score.json' not found. Please make sure it is saved in the same folder.")