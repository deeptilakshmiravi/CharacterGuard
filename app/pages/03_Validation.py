import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="CharacterGuard | Research Validation", page_icon="🧪", layout="wide")

st.title("🧪 Research Validation & Model Accuracy")
st.markdown("This dashboard evaluates the alignment between **Human Ground Truth** and **Gemini Flash 3 Judge**.")

# --- 1. File Upload ---
st.sidebar.header("Upload Results")
uploaded_file = st.sidebar.file_uploader("Upload the final_graded_results.csv", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Ensure necessary columns exist
    if 'judge_score' in df.columns and 'ai_score' in df.columns:
        
        # --- 2. Calculation Logic ---
        # Instead of exact match, we check if both human and AI agreed it was Unsafe (> 3) or Safe (<= 3)
        df['human_unsafe'] = df['judge_score'] > 3
        df['ai_unsafe'] = df['ai_score'] > 3
        df['is_aligned'] = (df['human_unsafe'] == df['ai_unsafe'])
        
        accuracy = (df['is_aligned'].sum() / len(df)) * 100
        
        # --- 3. Top Level Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rows Evaluated", len(df))
        col2.metric("Safety Alignment Rate", f"{accuracy:.1f}%")
        col3.metric("Dataset Source", "Zenodo / arXiv:2512.01247")
        
        st.divider()
        
        # --- 4. Visualization Sections ---
        left_chart, right_chart = st.columns(2)
        
        with left_chart:
            st.subheader("📊 Category Distribution")
            # Showing the count of different types of violations found
            if 'judge_category' in df.columns:
                cat_counts = df['judge_category'].value_counts().reset_index()
                cat_counts.columns = ['Category', 'Count']
                fig_bar = px.bar(cat_counts, x='Count', y='Category', orientation='h', 
                                 color='Count', color_continuous_scale='Reds',
                                 title="Frequency of Safety Violations (Human Labeled)")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.warning("Column 'judge_category' not found for distribution chart.")
            
        with right_chart:
            st.subheader("🎯 Confusion Matrix")
            # Calculate TP, TN, FP, FN manually so we don't need new libraries
            tp = ((df['human_unsafe'] == True) & (df['ai_unsafe'] == True)).sum()
            tn = ((df['human_unsafe'] == False) & (df['ai_unsafe'] == False)).sum()
            fp = ((df['human_unsafe'] == False) & (df['ai_unsafe'] == True)).sum()
            fn = ((df['human_unsafe'] == True) & (df['ai_unsafe'] == False)).sum()

            # Create a 2x2 matrix for Plotly
            z = [[tn, fp], [fn, tp]]
            x = ['AI: Safe', 'AI: Unsafe']
            y = ['Human: Safe', 'Human: Unsafe']

            fig_cm = px.imshow(z, text_auto=True, x=x, y=y,
                               color_continuous_scale='Blues',
                               title="True/False Positives & Negatives")
            st.plotly_chart(fig_cm, use_container_width=True)

        st.divider()
        
        # --- 5. The Error Analysis Table ---
        st.subheader("🧐 Deep-Dive: Disagreement Examples")
        st.markdown("These are rows where the AI score differed from the human score.")
        
        # Filter for rows where they disagreed
        disagreements = df[df['judge_score'] != df['ai_score']]
        
        if not disagreements.empty:
            # Display relevant columns if they exist
            display_cols = [col for col in ['description', 'question', 'answer', 'judge_score', 'ai_score'] if col in df.columns]
            st.dataframe(disagreements[display_cols].head(10), use_container_width=True)
        else:
            st.success("Perfect alignment! No disagreements found in this dataset.")

    else:
        st.error("The uploaded CSV is missing 'judge_score' or 'ai_score' columns. Please ensure Member 1 has processed the data correctly.")
        
else:
    # --- Empty State ---
    st.info("Waiting for data. Please upload the evaluated dataset after it has been processed by the Gemini Backend.")
    
    st.markdown("""
    ### How to prepare this data:
    1. Run the `validation_sample.csv` through the offline script.
    2. Ensure the final CSV has the columns: `question`, `answer`, `judge_score` (human truth), and `ai_score` (model output).
    3. Upload that finished file here to generate the accuracy charts.
    """)