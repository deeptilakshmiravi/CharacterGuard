import csv
import io
import re

TOXIC_WORDS = [r"badword1", r"badword2", r"dangerous", r"unsafe"]

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