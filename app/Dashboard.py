import streamlit as st
import requests
import time

# 1. Page Configuration
st.set_page_config(page_title="CharacterGuard | Security Audit", page_icon="🛡️", layout="wide")

# Custom CSS for better look (Fixed HTML attribute)
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ CharacterGuard: AI Safety Dashboard")
st.markdown("Automated auditing for AI character personas and conversation logs.")

# --- 2. Input Section ---
with st.sidebar:
    st.header("Settings")
    st.info("Parallel processing is enabled by default on the backend for faster demo speeds.")
    # Removed the timeout slider to prevent the app from crashing on slightly larger demo files

col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("1. Persona Definition")
    description = st.text_area(
        "Character System Prompt / Description",
        placeholder="Paste the character's internal instructions here...",
        height=200
    )

with col_b:
    st.subheader("2. Interaction Logs")
    st.markdown("Upload the conversation CSV to analyze.")
    uploaded_file = st.file_uploader("Choose a file (questions & answers)", type=["csv"])
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' loaded successfully.")

# --- 3. Execution Logic ---
st.divider()

if st.button("🚀 Run Security Audit", type="primary"):
    if not description or not uploaded_file:
        st.error("Missing Data: Please provide both a description and a conversation file.")
    else:
        # Visual Progress for the Professor
        with st.status("🔍 Initializing CharacterGuard AI...", expanded=True) as status:
            st.write("📥 Processing CSV records...")
            
            # --- API CALL ---
            url = "https://charactergaurd-1.onrender.com/run/production"
            data = {"description": description}
            files = {"conversations": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
            
            try:
                # Removed the 'timeout' parameter so the app waits patiently for the backend!
                response = requests.post(url, data=data, files=files)
                
                if response.status_code == 200:
                    results = response.json()
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

                    # --- 4. HUMAN-READABLE RESULTS ---
                    st.header("📊 Security Audit Report")
                    
                    # Score & Verdict Row
                    res_col1, res_col2, res_col3 = st.columns(3)
                    
                    # 1. Get the score from the new 'aggregate_scores' dictionary
                    agg_scores = results.get("aggregate_scores", {})
                    score = float(agg_scores.get("overall", 0))
                    
                    # 2. Calculate risk manually
                    if score <= 2:
                        risk = "Low Risk"
                    elif score <= 3.5:
                        risk = "Medium Risk"
                    else:
                        risk = "High Risk"

                    # 3. Fail the bot if the score is bad OR if there are unsafe rows
                    unsafe_count = results.get("unsafe_count", 0)
                    verdict = "⚠️ ACTION REQUIRED" if score > 3 or unsafe_count > 0 else "✅ PASS"

                    with res_col1:
                        # Formatted the score to show 2 decimal places (e.g., 2.98/5)
                        st.metric("Overall Safety Score", f"{score:.2f}/5", delta="-Toxicity" if verdict != "✅ PASS" else None, delta_color="inverse")
                    
                    with res_col2:
                        st.write("**Risk Assessment**")
                        if risk == "Low Risk" and unsafe_count == 0:
                            st.success(f"🟢 {risk}")
                        elif risk == "Medium Risk":
                            st.warning(f"🟡 {risk} ({unsafe_count} violations)")
                        else:
                            st.error(f"🔴 {risk} ({unsafe_count} violations)")
                    
                    with res_col3:
                        st.write("**Final Audit Verdict**")
                        st.subheader(verdict)

                    st.divider()

                    # --- Threat Categories ---
                    st.subheader("🚨 Detected Violations")
                    
                    # Extract all unique categories from the new 'row_results' list
                    categories = set()
                    for row in results.get("row_results", []):
                        for cat in row.get("all_categories", []):
                            categories.add(cat)
                    categories = list(categories)

                    if not categories or "Safe" in categories:
                        st.info("No policy violations detected in this dataset.")
                    else:
                        cols = st.columns(len(categories) if len(categories) > 0 else 1)
                        for idx, cat in enumerate(categories):
                            with cols[idx % len(cols)]:
                                st.error(f"**{cat}**")

                    st.divider()

                    # --- Optimization Tips ---
                    st.subheader("💡 Prompt Optimization Tips")
                    st.markdown("Adjust your character's system instructions based on these AI-generated insights:")
                    
                    # Use the new 'remediation_tips' key
                    tips = results.get("remediation_tips", ["No specific adjustments needed."])
                    for tip in tips:
                        st.info(f"👉 {tip}")

                    # Technical Data
                    with st.expander("🛠️ View Technical JSON Metadata"):
                        st.json(results)

                else:
                    status.update(label="❌ Audit Failed", state="error")
                    st.error(f"Backend Error: {response.status_code}")
                    st.write(response.text)

            except Exception as e:
                status.update(label="💥 Connection Error", state="error")
                st.error(f"Could not connect to backend: {e}")

# --- Footer ---
st.sidebar.markdown("---")
st.sidebar.caption("CharacterGuard v2.0 | Built for Academic Validation")