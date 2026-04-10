import csv
import io
import re

TOXIC_WORDS = [
    # Specific test words to ensure the demo works with your CSV
    r"FBI", r"address", r"badword1", r"badword2",
    
    # Real-world security & safety terms for a professional look
    r"scam", r"phishing", r"malware", r"hack", r"breach",
    r"password", r"credit card", r"social security", r"illegal"
]

def sanitize_csv(uploaded_file):
    decoded = uploaded_file.read().decode("utf-8").splitlines()
    reader = csv.reader(decoded)
    cleaned_rows = [row for row in reader if any(cell.strip() for cell in row)]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(cleaned_rows)
    return output.getvalue(), cleaned_rows

def flag_unsafe(text):
    flagged = text
    for pattern in TOXIC_WORDS:
        flagged = re.sub(
            pattern, 
            lambda m: f'<span style="color:red;font-weight:bold">{m.group(0)}</span>', 
            flagged, 
            flags=re.IGNORECASE
        )
    return flagged