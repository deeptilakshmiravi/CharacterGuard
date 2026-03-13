import streamlit as st
import json
import os

st.set_page_config(page_title="Comparison View", layout="wide", page_icon="⚖️")

st.title("⚖️ Before vs. After Comparison")
st.write("Compare how the baseline model and the hardened model handle the exact same attack.")
st.divider()

# Helper function to load JSON files from the main folder
def load_transcript(filename):
    # This tells Python to look one folder up from 'pages'
    file_path = os.path.join(os.path.dirname(__file__), '..', filename)
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

# Load the data
before_data = load_transcript("before_transcript.json")
after_data = load_transcript("after_transcript.json")

# Safety net: If the files are missing, tell the user gracefully
if not before_data or not after_data:
    st.warning("⚠️ Waiting for Backend Team. Please ensure 'before_transcript.json' and 'after_transcript.json' exist in the main folder.")
    st.stop()

# Layout the side-by-side columns
col1, col2 = st.columns(2)

# --- LEFT COLUMN (Before) ---
with col1:
    st.subheader("🔴 Baseline Model (Before)")
    st.caption(f"Category: `{before_data.get('category')}` | Attack ID: `{before_data.get('attack_id')}`")
    
    # Loop through the messages array dynamically
    for msg in before_data.get("messages", []):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.error(msg["content"]) # Red bubble to show failure

# --- RIGHT COLUMN (After) ---
with col2:
    st.subheader("🟢 Hardened Model (After)")
    st.caption(f"Category: `{after_data.get('category')}` | Attack ID: `{after_data.get('attack_id')}`")
    
    # Loop through the messages array dynamically
    for msg in after_data.get("messages", []):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.write(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.success(msg["content"]) # Green bubble to show success