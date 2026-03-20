import streamlit as st
import requests
import time

st.set_page_config(page_title="Run Tests | CharacterGuard", layout="wide")

st.markdown("""
    <style>
    header, .stApp { background-color: #0f172a !important; }
    h1, h2, h3, p, span, label { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #020617 !important; }
    .stButton>button { width: 100%; background-color: #38bdf8; color: white; font-weight: bold; border: none; padding: 0.5rem; border-radius: 8px; }
    .stButton>button:hover { background-color: #0ea5e9; border: none; }
    hr { border-color: #334155 !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Execute Adversarial Tests")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Test Configuration")
    test_type = st.selectbox("Select Attack Category", ["Prompt Injection", "Persona Drift", "Compliance Bypass", "All Tests"])
    model_target = st.text_input("Target API Endpoint (Optional)", placeholder="https://api.openai.com/v1...")
    
    if st.button("Start Security Scan"):
        with st.status("Connecting to CharacterGuard API...", expanded=True) as status:
            try:
                payload = {"test_type": test_type, "target_api": model_target}
                res = requests.post("https://charactergaurd-1.onrender.com/run-test", json=payload, timeout=15)
                
                if res.status_code == 200:
                    st.write("Scan initiated...")
                    time.sleep(2)
                    status.update(label="Scan Complete!", state="complete", expanded=False)
                    st.success("Test run finished. Check the Dashboard for updated scores.")
                else:
                    status.update(label="API Error", state="error")
            except:
                status.update(label="Connection Failed", state="error")
                st.error("Make sure backend is awake at Render URL.")

with col2:
    st.info("**Note:** Running a full scan sends multiple adversarial prompts and takes ~30-60 seconds.")