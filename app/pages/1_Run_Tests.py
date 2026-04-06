import streamlit as st
import csv
import io
import re
from app.api_client import run_production  # bridge to backend

st.title("Run Character Test")

# --- Input ---
description = st.text_area("Character Description")
uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# --- Helper: Regex sanitizer for toxic/unsafe words ---
TOXIC_WORDS = [
    r"badword1", r"badword2", r"dangerous", r"unsafe"  # example patterns
]

def flag_unsafe(text):
    """
    Returns text with unsafe/toxic words highlighted in red.
    """
    flagged = text
    for pattern in TOXIC_WORDS:
        flagged = re.sub(
            pattern, 
            lambda m: f'<span style="color:red;font-weight:bold">{m.group(0)}</span>', 
            flagged, 
            flags=re.IGNORECASE
        )
    return flagged

# --- Run Test ---
if st.button("Run Test") and uploaded_file:

    # Read + clean CSV
    decoded = uploaded_file.read().decode("utf-8").splitlines()
    reader = csv.reader(decoded)
    cleaned_rows = [row for row in reader if any(cell.strip() for cell in row)]

    # Flag unsafe words for live preview (your contribution!)
    preview_rows = []
    for row in cleaned_rows:
        flagged_row = [flag_unsafe(cell) for cell in row]
        preview_rows.append(flagged_row)

    # Show preview in Streamlit
    st.subheader("Preview: Flagged Unsafe Words")
    for row in preview_rows:
        st.markdown(" | ".join(row), unsafe_allow_html=True)

    # Convert back to CSV string
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(cleaned_rows)
    cleaned_csv = output.getvalue()

    # Send to backend
    result = run_production(description, cleaned_csv)

    # Save results to session_state for dashboard
    st.session_state["results"] = result

    st.success("✅ Done! Go to Results Dashboard 👉")
