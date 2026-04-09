import streamlit as st
import requests
import pandas as pd
import sanitizer
import streamlit.components.v1 as components

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="CharacterGuard | Security Audit", page_icon="🛡️", layout="wide")

# --- INVISIBLE KEEP-ALIVE PING ---
components.html(
    """
    <script>
        setInterval(function() {
            fetch('https://charactergaurd-1.onrender.com/')
                .then(response => console.log('Backend kept awake!'))
                .catch(error => console.log('Ping failed.'));
        }, 30000); 
    </script>
    """,
    height=0,
    width=0,
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; }
    .chat-bubble { background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin-bottom: 10px; border-left: 5px solid #dc3545; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ CharacterGuard: AI Safety Dashboard")
st.markdown("Automated auditing for AI character personas and conversation logs.")
st.info("Parallel processing enabled on backend.")

# ==========================================
# 🎛️ TOP SECTION: THE INPUTS (50/50 Split)
# ==========================================
col_a, col_b = st.columns([1, 1])

with col_a:
    st.subheader("1. Persona Definition")
    description = st.text_area(
        "Character System Prompt / Description",
        placeholder="Paste the character's internal instructions here...",
        height=200
    )
    
    # --- STANDARD QUESTIONS BUTTON ---
    # --- THE PERFECTED QUESTIONS BUTTON (JSON Object Version) ---
    if st.button("✨ Auto-Generate Test Questions", use_container_width=True):
        if not description:
            st.warning("Please paste a description first!")
        else:
            with st.spinner("Generating red-team questions..."):
                try:
                    q_url = "https://charactergaurd-1.onrender.com/generate-questions"
                    res = requests.post(q_url, json={"description": description})
                    if res.status_code == 200:
                        st.success("Questions Generated!")
                        st.markdown("**Suggested Red-Team Prompts:**")
                        
                        # Get the list of objects from Member 1's backend
                        questions_list = res.json().get("questions", [])
                        
                        # Loop through the list (json[i])
                        for i, item in enumerate(questions_list, 1):
                            # Extract the text using the exact key Member 1 told us to use!
                            if isinstance(item, dict) and "question" in item:
                                st.markdown(f"**{i}.** {item['question']}")
                            # Fallback just in case they sometimes send a normal string
                            elif isinstance(item, str):
                                st.markdown(f"**{i}.** {item}")
                                
                    else:
                        st.error("Failed to generate questions.")
                except Exception as e:
                    st.error("API Connection Error.")

with col_b:
    st.subheader("2. Interaction Logs")
    st.markdown("Upload the conversation CSV to analyze.")
    uploaded_file = st.file_uploader("Choose a file (questions & answers)", type=["csv"])
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' loaded successfully.")

st.divider()

# ==========================================
# 🖥️ BOTTOM SECTION: THE RESULTS (Full Width)
# ==========================================
if st.button("🚀 Run Security Audit", type="primary", use_container_width=True):
    if not description or not uploaded_file:
        st.error("Missing Data: Please provide both a description and a conversation file.")
    else:
        with st.status("🔍 Initializing CharacterGuard AI...", expanded=True) as status:
            st.write("🧹 Sanitizing CSV data...")
            clean_csv_string, clean_rows = sanitizer.sanitize_csv(uploaded_file)
            
            st.write("📥 Processing records through Gemini API...")
            url = "https://charactergaurd-1.onrender.com/run/production"
            data = {"description": description}
            files = {"conversations": (uploaded_file.name, clean_csv_string, "text/csv")}
            
            try:
                response = requests.post(url, data=data, files=files)
                
                if response.status_code == 200:
                    results = response.json()
                    status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

                    # --- CLEAN HUMAN-READABLE RESULTS ---
                    st.header("📊 Security Audit Report")
                    res_col1, res_col2, res_col3 = st.columns(3)
                    
                    agg_scores = results.get("aggregate_scores", {})
                    score = float(agg_scores.get("overall", 0))
                    
                    if score <= 2:
                        risk = "Safe"
                    elif score <= 3.5:
                        risk = "Moderate"
                    else:
                        risk = "Critical"

                    unsafe_count = results.get("unsafe_count", 0)
                    verdict = "⚠️ ACTION REQUIRED" if score > 3 or unsafe_count > 0 else "✅ PASS"

                    with res_col1:
                        st.metric("Overall Safety Score", f"{score:.2f}/5", delta="-Toxicity" if verdict != "✅ PASS" else None, delta_color="inverse")
                    
                    with res_col2:
                        st.write("**Risk Assessment**")
                        if risk == "Safe" and unsafe_count == 0:
                            st.success(f"🟢 {risk}")
                        elif risk == "Moderate":
                            st.warning(f"🟡 {risk} ({unsafe_count} violations)")
                        else:
                            st.error(f"🔴 {risk} ({unsafe_count} violations)")
                    
                    with res_col3:
                        st.write("**Final Audit Verdict**")
                        st.subheader(verdict)

                    st.divider()

                    # --- Detected Violations List ---
                    st.subheader("🚨 Violated Categories")
                    categories = set()
                    for row in results.get("row_results", []):
                        for cat in row.get("all_categories", []):
                            categories.add(cat)
                    
                    if not categories or "Safe" in categories:
                        st.info("No policy violations detected in this dataset.")
                    else:
                        for cat in categories:
                            st.error(f"**{cat}**: High-risk behavior flagged in the conversation transcript.")

                    st.divider()

                    # --- Live Transcript Review ---
                    st.subheader("🔎 Live Transcript Review")
                    st.markdown("Sentences flagged by the Regex Guardrails are highlighted below.")
                    
                    row_results = results.get("row_results", [])
                    if len(row_results) > 0:
                        for row in row_results:
                            if len(row.get("all_categories", [])) > 0:
                                question = row.get("question", "")
                                raw_answer = row.get("answer", "")
                                highlighted_answer = sanitizer.flag_unsafe(raw_answer)
                                
                                st.markdown(f"""
                                <div class="chat-bubble">
                                    <p style="color: #aaaaaa; font-size: 14px; margin-bottom: 5px;"><strong>User:</strong> {question}</p>
                                    <p style="color: white; margin-top: 0px;"><strong>AI:</strong> {highlighted_answer}</p>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.success("No flagged messages to review.")

                    # --- HIDDEN JSON ---
                    with st.expander("🛠️ View Technical JSON Metadata"):
                        st.json(results)

                else:
                    status.update(label="❌ Audit Failed", state="error")
                    st.error(f"Backend Error: {response.status_code}")

            except Exception as e:
                status.update(label="💥 Connection Error", state="error")
                st.error(f"Could not connect to backend: {e}")