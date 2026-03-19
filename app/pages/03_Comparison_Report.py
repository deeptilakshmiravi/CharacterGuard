import streamlit as st
import json
import os

st.set_page_config(page_title="Comparison | CharacterGuard", layout="wide")

# Matching Dark CSS
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; }
    header, [data-testid="stSidebar"] { background-color: #020617 !important; }
    h1, h2, h3, p, span, b { color: #ffffff !important; }
    .stInfo, .stSuccess { background-color: #1e293b !important; border: 1px solid #334155 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

def load_transcript(filename):
    # Member 6 puts files in data/reports/
    file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'reports', filename)
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
            return data.get("transcript", [])
    except:
        return None

st.title("⚖️ Comparison Report")
st.write("Side-by-side analysis of Baseline vs. Hardened responses.")
st.divider()

# Loading the files Member 6 is responsible for
before_data = load_transcript("before_transcript.json")
after_data = load_transcript("after_transcript.json")

if before_data and after_data:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔴 Baseline")
        for msg in before_data:
            st.info(f"**{msg['role'].capitalize()}:** {msg['content']}")
    with c2:
        st.subheader("🟢 Hardened")
        for msg in after_data:
            st.success(f"**{msg['role'].capitalize()}:** {msg['content']}")
else:
    st.warning("⚠️ Waiting for transcript data from Member 6. Ensure before_transcript.json is in data/reports/")