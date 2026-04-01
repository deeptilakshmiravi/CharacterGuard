import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Platform Validation", page_icon="⚖️", layout="wide")

st.title("⚖️ Platform Validation")
st.markdown("Upload a ground-truth dataset to validate the CharacterGuard scoring engine.")

# --- 1. File Upload ---
st.info("Upload a CSV dataset containing: `description`, `question`, `answer`, `judge_score`, `judge_category`, `NSFW`.")
uploaded_file = st.file_uploader("Upload Validation Dataset (CSV)", type=["csv"])

if st.button("Run Validation", type="primary"):
    if not uploaded_file:
        st.warning("Please upload a CSV dataset to begin validation.")
    else:
        with st.spinner("Validating against ground truth..."):
            
            # Esther's Validation Endpoint
            url = "https://charactergaurd-1.onrender.com/run/validation"
            
            # Esther requested the field be named exactly "dataset"
            files = {"dataset": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            
            try:
                response = requests.post(url, files=files)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Validation Complete!")
                    
                    # --- 2. Top-Level Metrics ---
                    st.subheader("📊 Validation Metrics")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    agreement_rate = data.get('ground_truth_agreement_rate', 0) * 100
                    match_rate = data.get('category_match_rate', 0) * 100
                    
                    col1.metric("Ground Truth Agreement", f"{agreement_rate:.1f}%")
                    col2.metric("Category Match Rate", f"{match_rate:.1f}%")
                    col3.metric("Total Rows Evaluated", data.get('total_rows', 0))
                    col4.metric("Unsafe Count", data.get('unsafe_count', 0))
                    
                    st.divider()
                    
                    # --- 3. Per-Row Breakdown Table ---
                    st.subheader("Detailed Row Comparison")
                    
                    if "row_results" in data:
                        rows = data["row_results"]
                        table_data = []
                        for row in rows:
                            cat_match = "✅" if row.get('ground_truth_category') in row.get('all_categories', []) else "⚠️"
                            
                            table_data.append({
                                "Question": row.get("question", "")[:50] + "...",
                                "Our Score": row.get("scores", {}).get("overall"),
                                "Ground Truth": row.get("ground_truth_score"),
                                "Score Delta": row.get("score_delta"),
                                "Our Categories": ", ".join(row.get("all_categories", [])),
                                "True Category": row.get("ground_truth_category"),
                                "Match": cat_match
                            })
                            
                        df = pd.DataFrame(table_data)
                        
                        # Style the dataframe to highlight delta
                        st.dataframe(
                            df.style.map(
                                lambda val: 'color: red' if isinstance(val, (int, float)) and val < 0 else ('color: green' if isinstance(val, (int, float)) and val > 0 else ''), 
                                subset=['Score Delta']
                            ),
                            use_container_width=True,
                            hide_index=True
                        )
                    else:
                        st.write("No row-level data returned.")
                        
                else:
                    st.error(f"Backend Error: {response.status_code}")
                    st.write(response.text)
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to connect: {e}")