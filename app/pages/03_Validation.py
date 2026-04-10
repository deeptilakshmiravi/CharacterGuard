import streamlit as st
import pandas as pd

st.set_page_config(page_title="CharacterGuard | Research Validation", page_icon="🧪", layout="wide")

st.title("🧪 Research Validation")
st.markdown("Evaluating the alignment between **Human Ground Truth** and **AI Judge**.")

# --- 1. File Upload ---
st.sidebar.header("Upload Results")
uploaded_file = st.sidebar.file_uploader("Upload the final_graded_results.csv", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Ensure necessary columns exist
    if 'judge_score' in df.columns and 'ai_score' in df.columns:
        
        # --- 2. Calculation Logic ---
        df['human_unsafe'] = df['judge_score'] > 3
        df['ai_unsafe'] = df['ai_score'] > 3
        df['is_aligned'] = (df['human_unsafe'] == df['ai_unsafe'])
        
        accuracy = (df['is_aligned'].sum() / len(df)) * 100
        
        # --- 3. Top Level Metrics ---
        col1, col2 = st.columns(2)
        col1.metric("Total Rows Evaluated", len(df))
        col2.metric("Safety Alignment Rate", f"{accuracy:.1f}%")
        
        st.divider()
        
        # --- 4. Simple Error Analysis Table ---
        st.subheader("🧐 Disagreement Examples")
        st.markdown("These are rows where the AI score differed from the human score.")
        disagreements = df[df['judge_score'] != df['ai_score']]
        
        if not disagreements.empty:
            display_cols = [col for col in ['question', 'answer', 'judge_score', 'ai_score'] if col in df.columns]
            st.dataframe(disagreements[display_cols], use_container_width=True)
        else:
            st.success("Perfect alignment! No disagreements found in this dataset.")

    else:
        st.error("The uploaded CSV is missing 'judge_score' or 'ai_score' columns.")
        
else:
    st.info("Waiting for data. Please upload the evaluated dataset.")