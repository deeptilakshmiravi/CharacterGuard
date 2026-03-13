import streamlit as st
import json
import os

# 1. Page Configuration
st.set_page_config(page_title="Comparison Report | CharacterGuard", layout="wide")

# 2. Ultimate Dark CSS (Fixes the white bar and text)
st.markdown("""
    <style>
    /* Hide the white top bar and set background */
    header, .stApp { background-color: #0f172a !important; }
    
    /* Force ALL text to White */
    h1, h2, h3, p, span, div, label, b { color: #ffffff !important; }

    /* Sidebar Styling */
    [data-testid="stSidebar"] { background-color: #020617 !important; }
    
    /* Custom Styling for Chat Bubbles */
    .stInfo, .stSuccess {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        color: #ffffff !important;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }

    /* Fix Divider Color */
    hr { border-color: #334155 !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. Secure File Loading
def load_transcript(filename):
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reports', filename)
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            # SAFETY CHECK: If the JSON doesn't have 'transcript', return an empty list
            return data.get("transcript", [])
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# 4. Header
st.title("⚖️ Comparison Report")
st.write("Comparing Baseline vs. Hardened AI Responses")
st.divider()

# 5. Load and Display Data
before_list = load_transcript("before_transcript.json")
after_list = load_transcript("after_transcript.json")

if before_list is not None and after_list is not None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔴 Baseline (Before)")
        if not before_list:
            st.warning("No transcript data found in before_transcript.json")
        for msg in before_list:
            role = msg.get('role', 'Unknown').capitalize()
            content = msg.get('content', 'No content available')
            st.markdown(f"**{role}:**")
            st.info(content)

    with col2:
        st.subheader("🟢 Hardened (After)")
        if not after_list:
            st.warning("No transcript data found in after_transcript.json")
        for msg in after_list:
            role = msg.get('role', 'Unknown').capitalize()
            content = msg.get('content', 'No content available')
            st.markdown(f"**{role}:**")
            st.success(content)
else:
    st.error("⚠️ Data files missing in data/reports/")