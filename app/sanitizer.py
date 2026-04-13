import io
import csv

def sanitize_csv(uploaded_file):
    """
    Reads an uploaded CSV file, handles potential encoding conflicts (UTF-8/Latin-1),
    strips whitespace, and returns a sanitized CSV string and a list of rows.
    """
    # 1. Encoding Logic
    # Attempts to read as UTF-8, with a fallback to latin-1 to handle 
    # Windows-specific characters like dashes (—) or smart quotes (’)
    try:
        content = uploaded_file.read().decode("utf-8")
    except UnicodeDecodeError:
        # Reset the file pointer to the start of the file before the second attempt
        uploaded_file.seek(0)
        content = uploaded_file.read().decode("latin-1")
    except AttributeError:
        # Handle cases where the input might already be a string
        content = str(uploaded_file)

    # 2. Parsing and Cleaning
    lines = content.splitlines()
    reader = csv.reader(lines)
    
    sanitized_rows = []
    for row in reader:
        # Remove whitespace from each cell and ignore rows that are completely empty
        clean_row = [cell.strip() for cell in row]
        if any(cell for cell in clean_row if cell):
            sanitized_rows.append(clean_row)
            
    # 3. String Reconstruction
    # Rebuilds the cleaned data into a standardized CSV string format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(sanitized_rows)
    
    # Return both the CSV string (for API transmission) and the list (for local display)
    return output.getvalue(), sanitized_rows