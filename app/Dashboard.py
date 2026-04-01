import streamlit as st
import requests
import pandas as pd

# Configure the page
st.set_page_config(page_title="CharacterGuard | Production", page_icon="🛡️", layout="wide")

st.title("🛡️ CharacterGuard: Production Evaluation")
st.markdown("Upload a character's persona and their conversation history to evaluate their safety.")

# --- 1. User Inputs ---
st.subheader("1. Character Details")
description = st.text_area(
    "Character Description",
    placeholder="Paste the character's persona, system prompt, or description here...",
    height=150
)

st.subheader("2. Conversation History")
st.info("Upload a CSV file containing the interaction history. It MUST have exactly two columns: `questions` (user input) and `answers` (AI response).")
uploaded_file = st.file_uploader("Upload Conversations.csv", type=["csv"])

# --- 2. API Execution ---
st.write("---")
if st.button("Run Safety Evaluation", type="primary"):
    
    if not description:
        st.warning("Please enter a character description.")
    elif not uploaded_file:
        st.warning("Please upload a conversations CSV file.")
    else:
        with st.spinner("Analyzing conversations against safety parameters..."):
            
            # Member 1's Production Endpoint
            url = "https://charactergaurd-1.onrender.com/run/production"
            
            # Multipart Form-Data
            data = {"description": description}
            files = {"conversations": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            
            try:
                response = requests.post(url, data=data, files=files)
                
                if response.status_code == 200:
                    st.success("Analysis Complete!")
                    results = response.json()
                    
                    # Display Raw JSON temporarily
                    st.subheader("Raw Evaluation Results")
                    st.json(results)
                    
                else:
                    st.error(f"Backend Error (Status {response.status_code})")
                    st.write(response.text)
                    
            except requests.exceptions.RequestException as e:
                st.error("Failed to connect to backend. Please ensure the backend server is awake.")