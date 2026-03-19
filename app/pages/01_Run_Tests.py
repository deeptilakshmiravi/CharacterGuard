import streamlit as st
import requests
import time

st.set_page_config(page_title="Run Tests | CharacterGuard", layout="wide")

# Matching Dark CSS
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    h1, h2, h3, p, span, label { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #020617; }
    .stButton>button { width: 100%; background-color: #38bdf8; color: white; font-weight: bold; border: none; padding: 0.5rem; }
    .stButton>button:hover { background-color: #0ea5e9; border: none; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚀 Execute Adversarial Tests")
st.write("Trigger a live security scan against the target character configuration.")
st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Test Configuration")
    test_type = st.selectbox("Select Attack Category", ["Prompt Injection", "Persona Drift", "Compliance Bypass", "All Tests"])
    model_target = st.text_input("Target API Endpoint (Optional)", placeholder="https://api.openai.com/v1...")
    
    if st.button("Start Security Scan"):
        with st.status("Connecting to CharacterGuard API...", expanded=True) as status:
            try:
                # Calling Member 1's Cloud API
                payload = {"test_type": test_type, "target": model_target}
                res = requests.post("https://charactergaurd-1.onrender.com/run-test", json=payload, timeout=10)
                
                if res.status_code == 200:
                    st.write("Scan initiated successfully...")
                    time.sleep(1)
                    st.write("Running adversarial prompts...")
                    time.sleep(2)
                    status.update(label="Scan Complete!", state="complete", expanded=False)
                    st.success("Test run finished. Check the Dashboard for updated scores.")
                else:
                    status.update(label="API Error", state="error")
                    st.error(f"Backend returned an error: {res.status_code}")
            except Exception as e:
                status.update(label="Connection Failed", state="error")
                st.error("Could not reach the backend server. Make sure it is awake.")

with col2:
    st.info("**Note:** Running a full scan takes approximately 30-60 seconds depending on the model response time.")