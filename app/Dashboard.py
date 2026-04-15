import streamlit as st
import requests
import pandas as pd
import sanitizer
import streamlit.components.v1 as components
import io

# --- PASTE PARSER FUNCTION (SPEAKER-AWARE) ---
def parse_pasted_chat(raw_text, user_name, char_name):
    """Smarter parser that handles multi-paragraph responses by looking for speaker names."""
    lines = raw_text.split('\n')
    
    questions = []
    answers = []
    
    current_speaker = None
    current_text = []
    
    for line in lines:
        clean_line = line.strip()
        
        # Check if the line is exactly the User's name
        if clean_line.lower() == user_name.strip().lower():
            if current_speaker == "char" and current_text:
                answers.append("\n\n".join(current_text).strip())
            current_speaker = "user"
            current_text = []
            
        # Check if the line is exactly the Character's name
        elif clean_line.lower() == char_name.strip().lower():
            if current_speaker == "user" and current_text:
                questions.append("\n\n".join(current_text).strip())
            current_speaker = "char"
            current_text = []
            
        # If it's not a name, it's dialogue
        else:
            if current_speaker and clean_line:
                current_text.append(clean_line)
                
    # Catch the very last AI answer at the end of the copy-paste
    if current_speaker == "char" and current_text:
        answers.append("\n\n".join(current_text).strip())
        
    # Ensure our lists are the exact same length to prevent dataframe errors
    min_len = min(len(questions), len(answers))
    return pd.DataFrame({
        'question': questions[:min_len], 
        'answer': answers[:min_len]
    })

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="CharacterGuard | Security Audit", page_icon="🛡️", layout="wide")

# --- REMOVE TOP WHITESPACE ---
st.markdown("""
    <style>
        .block-container {
            padding-top: 1.5rem;
        }
    </style>
""", unsafe_allow_html=True)

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

# --- 2. SESSION STATE MEMORY ---
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'description' not in st.session_state:
    st.session_state.description = ""
if 'questions_data' not in st.session_state:
    st.session_state.questions_data = []
if 'parsed_csv_string' not in st.session_state:
    st.session_state.parsed_csv_string = None

def go_to_step(step):
    st.session_state.current_step = step

# --- 3. UI HEADER & PROGRESS BAR ---
st.title("🛡️ CharacterGuard: AI Safety Dashboard")
st.markdown("Automated auditing for AI character personas and conversation logs.")

# Dynamic Progress Bar
steps = ["1. Define Character", "2. Generate Questions", "3. Run Security Audit"]
progress_val = int((st.session_state.current_step / 3) * 100)
st.progress(progress_val, text=f"Step {st.session_state.current_step} of 3: {steps[st.session_state.current_step-1]}")

# --- INSTRUCTIONS BLOCK ---
with st.expander("📖 How to use CharacterGuard", expanded=False):
    st.markdown("""
    **Follow this step-by-step process to audit your character:**
    1. **Define the Character:** Paste your character's system prompt or description in Step 1.
    2. **Generate Prompts:** The LLM will analyze the persona and return custom red-team questions.
    3. **Chat on Platform:** Take those generated questions, chat with your character, and bring the logs to Step 3.
    4. **Run the Audit:** Upload your CSV or Paste the chat in Step 3 and click **🚀 Run Security Audit** to get your final safety verdict!
    """)

st.divider()

# ==========================================
# 🎠 STEP 1: CHARACTER DESCRIPTION
# ==========================================
if st.session_state.current_step == 1:
    st.subheader("Step 1: Persona Definition")
    st.markdown("Paste your character's system prompt or description below to begin.")
    
    desc_input = st.text_area(
        "Character System Prompt / Description",
        value=st.session_state.description,
        placeholder="Paste the character's internal instructions here...",
        height=200
    )
    
    if st.button("✨ Generate Test Questions", type="primary"):
        if not desc_input:
            st.warning("Please paste a description first!")
        else:
            st.session_state.description = desc_input
            with st.spinner("Generating red-team questions..."):
                try:
                    q_url = "https://charactergaurd-1.onrender.com/generate-questions"
                    res = requests.post(q_url, json={"description": desc_input})
                    if res.status_code == 200:
                        st.session_state.questions_data = res.json().get("questions", [])
                        go_to_step(2)
                        st.rerun() 
                    else:
                        st.error("Failed to generate questions. Backend Error.")
                except Exception as e:
                    st.error(f"API Connection Error: {e}")

# ==========================================
# 🎠 STEP 2: QUESTIONS DISPLAY
# ==========================================
elif st.session_state.current_step == 2:
    st.subheader("Step 2: Generated Test Questions")
    st.info("💡 **Action Required:** Use these generated questions to chat with your character. Bring the responses to Step 3.")
    
    with st.container(border=True):
        if st.session_state.questions_data:
            for i, item in enumerate(st.session_state.questions_data, 1):
                if isinstance(item, dict) and "question" in item:
                    st.markdown(f"**{i}.** {item['question']}")
                elif isinstance(item, str):
                    st.markdown(f"**{i}.** {item}")
        else:
            st.warning("No questions were generated.")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("⬅️ Back to Edit", use_container_width=True):
            go_to_step(1)
            st.rerun()
    with col2:
        if st.button("Next Step: Upload Chat Logs ➡️", type="primary", use_container_width=True):
            go_to_step(3)
            st.rerun()

# ==========================================
# 🎠 STEP 3: UPLOAD & AUDIT
# ==========================================
elif st.session_state.current_step == 3:
    st.subheader("Step 3: Security Audit")
    
    col_back, col_space = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Back to Questions", use_container_width=True):
            go_to_step(2)
            st.rerun()
            
    st.markdown("How would you like to import your red-team testing logs?")
    
    # --- THE NEW TAB LAYOUT ---
    tab1, tab2 = st.tabs(["📝 Quick Paste (Recommended)", "📁 Upload CSV"])
    
    with tab1:
        st.write("Drag-select your conversation in the chat window, copy (Ctrl+C), and paste below.")
        
        # --- NEW: Speaker Labels ---
        col_u, col_c = st.columns(2)
        user_name = col_u.text_input("Your Username (as shown in chat):", value="User")
        char_name = col_c.text_input("Character's Name (as shown in chat):", value="Character")
        # ---------------------------

        pasted_text = st.text_area("Paste Chat Log Here:", height=200)
        
        if st.button("Parse and Preview"):
            if pasted_text:
                try:
                    parsed_df = parse_pasted_chat(pasted_text, user_name, char_name)
                    
                    if parsed_df.empty:
                        st.error("Could not find those exact names in the text. Please check spelling!")
                    else:
                        st.success("✅ Chat parsed successfully!")
                        st.dataframe(parsed_df, use_container_width=True)
                        
                        # Convert parsed dataframe to CSV string for the backend
                        csv_buffer = io.StringIO()
                        parsed_df.to_csv(csv_buffer, index=False)
                        st.session_state.parsed_csv_string = csv_buffer.getvalue()
                except Exception as e:
                    st.error("Oops! Couldn't parse the text. Ensure you copied the full alternating blocks.")

    with tab2:
        st.write("Upload the conversation CSV to analyze the character's behavior.")
        uploaded_file = st.file_uploader("Choose a CSV file (questions & answers)", type=["csv"])
        if uploaded_file:
            # Clear the pasted text state if they choose to upload a file instead
            st.session_state.parsed_csv_string = None

    # --- UNIFIED AUDIT SUBMISSION ---
    st.divider()
    if st.button("🚀 Run Security Audit", type="primary", use_container_width=True):
        csv_payload = None
        file_name = "pasted_chat.csv"
        
        # Check which method the user used
        if st.session_state.parsed_csv_string and not uploaded_file:
            csv_payload = st.session_state.parsed_csv_string
        elif uploaded_file:
            file_name = uploaded_file.name
            st.write("🧹 Sanitizing CSV data...")
            csv_payload, _ = sanitizer.sanitize_csv(uploaded_file)
            
        if not csv_payload:
            st.error("Please parse a pasted chat or upload a CSV file before running the audit.")
        else:
            with st.status("🔍 Initializing CharacterGuard AI...", expanded=True) as status:
                st.write("📥 Processing records through API...")
                url = "https://charactergaurd-1.onrender.com/run/production"
                data = {"description": st.session_state.description}
                files = {"conversations": (file_name, csv_payload, "text/csv")}
                
                try:
                    response = requests.post(url, data=data, files=files)
                    
                    if response.status_code == 200:
                        results = response.json()
                        status.update(label="✅ Analysis Complete!", state="complete", expanded=False)

                        # --- CLEAN UX RESULTS PAGE ---
                        st.header("📊 Security Audit Report")
                        res_col1, res_col2, res_col3 = st.columns(3)
                        row_results = results.get("row_results", [])

                        # --- GET GLOBAL VERDICT FIRST ---
                        global_verdict = "Safe"
                        if "llm_judge_verdict" in results:
                            global_verdict = results["llm_judge_verdict"]
                        else:
                            for row in row_results:
                                row_v = str(row.get("llm_judge_verdict", row.get("verdict", ""))).lower()
                                if "unsafe" in row_v:
                                    global_verdict = "Unsafe"
                                    break
                                elif "ambiguous" in row_v or "review" in row_v:
                                    global_verdict = "Needs Review"

                        # --- COLUMN 1: VERDICT BADGE ---
                        with res_col1:
                            st.subheader("🎯 Overall Verdict")
                            if str(global_verdict).lower() == "unsafe":
                                st.markdown(
                                    """
                                    <div style="background-color: #fde8e8; border: 1px solid #f8b4b4; color: #c81e1e; padding: 10px; border-radius: 8px; width: 100%; text-align: center; margin-bottom: 15px;">
                                        <strong style="font-size: 16px;">🚨 VERDICT: UNSAFE</strong>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            elif "review" in str(global_verdict).lower() or "ambiguous" in str(global_verdict).lower():
                                st.markdown(
                                    """
                                    <div style="background-color: #fdf6b2; border: 1px solid #fce96a; color: #723b13; padding: 10px; border-radius: 8px; width: 100%; text-align: center; margin-bottom: 15px;">
                                        <strong style="font-size: 16px;">⚠️ VERDICT: NEEDS REVIEW</strong>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )
                            else:
                                st.markdown(
                                    """
                                    <div style="background-color: #def7ec; border: 1px solid #84e1bc; color: #03543f; padding: 10px; border-radius: 8px; width: 100%; text-align: center; margin-bottom: 15px;">
                                        <strong style="font-size: 16px;">✅ VERDICT: SAFE</strong>
                                    </div>
                                    """, 
                                    unsafe_allow_html=True
                                )

                        # --- COLUMN 2: WHAT WENT WRONG ---
                        with res_col2:
                            st.subheader("🚩 What Went Wrong")
                            categories = set()
                            
                            for row in row_results:
                                cat = str(row.get("judge_category", "")).strip()
                                if cat and cat.lower() not in ["safe", "none", "n/a", ""]:
                                    categories.add(cat.title())
                                else:
                                    for c in row.get("all_categories", []):
                                        c_str = str(c).strip()
                                        if c_str and c_str.lower() not in ["safe", "none", "n/a", ""]:
                                            categories.add(c_str.title())
                            
                            if categories:
                                for cat in categories:
                                    st.markdown(f"• {cat}")
                            else:
                                if str(global_verdict).lower() == "safe":
                                    st.success("No violations detected.")
                                else:
                                    st.markdown("• Flagged for ambiguous behavior (Manual review required).")

                        # --- COLUMN 3: HOW TO FIX THIS ---
                        with res_col3:
                            st.subheader("🛠️ Action Items")
                            raw_tips = results.get("remediation_tips", [])
                            valid_tips = []
                            
                            ignore_phrases = ["no major concern", "none", "n/a", "no action needed", "safe"]
                            for tip in raw_tips:
                                tip_lower = str(tip).lower()
                                if not any(phrase in tip_lower for phrase in ignore_phrases):
                                    valid_tips.append(tip)

                            if valid_tips:
                                for tip in valid_tips:
                                    st.info(f"💡 {tip}")
                            elif "review" in str(global_verdict).lower():
                                st.info("💡 Review the specific conversation context. Borderline behavior detected.")
                            else:
                                st.success("Character persona is well-aligned.")

                        st.divider()

                        # --- ROW-BY-ROW BREAKDOWN (Below the Fold) ---
                        st.subheader("🔍 Row-by-Row Breakdown")
                        table_data = []
                        for row in row_results:
                            raw_q = str(row.get("question", ""))
                            q_trunc = raw_q[:57] + "..." if len(raw_q) > 60 else raw_q
                            verdict_badge = str(row.get("llm_judge_verdict", row.get("verdict", "Safe"))).title()
                            
                            category = row.get("judge_category")
                            if not category:
                                cat_list = row.get("all_categories", ["None"])
                                category = ", ".join(cat_list) if cat_list else "None"
                                
                            nsfw_val = row.get("nsfw", "No")
                            if isinstance(nsfw_val, bool):
                                nsfw_val = "Yes" if nsfw_val else "No"
                            
                            table_data.append({
                                "Question": q_trunc,
                                "Verdict": verdict_badge,
                                "Category Flagged": category,
                                "NSFW": str(nsfw_val).title()
                            })

                        if table_data:
                            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
                        else:
                            st.info("No conversation rows to display.")

                        with st.expander("🛠️ View Technical JSON Metadata"):
                            st.json(results)

                        st.divider()
                        if st.button("🔄 Audit Another Character", type="secondary"):
                            st.session_state.current_step = 1
                            st.session_state.description = ""
                            st.session_state.questions_data = []
                            st.session_state.parsed_csv_string = None
                            st.rerun()

                    else:
                        status.update(label="❌ Audit Failed", state="error")
                        st.error(f"Backend Error: {response.status_code}")

                except Exception as e:
                    status.update(label="💥 Connection Error", state="error")
                    st.error(f"Could not connect to backend: {e}")