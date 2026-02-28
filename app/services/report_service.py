import csv

def clean_text(text):
    """Clean text of encoding issues and special characters"""
    if not text:
        return ""

    # Convert to string if needed
    text = str(text)

    # Remove BOM and weird Unicode characters
    text = text.encode('utf-8', errors='replace').decode('utf-8')

    return text.strip()

def format_summary(data):
    """Format summary text/list by adding newlines for better readability in CSV"""
    if not data:
        return ""

    # Convert list to string if needed
    if isinstance(data, list):
        # Join list items with newlines - use "-" instead of "•" for better compatibility
        formatted_items = []
        for item in data:
            if item:
                clean_item = clean_text(item)
                formatted_items.append(f"- {clean_item}")

        return "\n".join(formatted_items).strip()

    # If it's already a string
    if isinstance(data, str):
        text = clean_text(data)
        # Add newlines after periods followed by space
        formatted = text.replace(". ", ".\n")
        return formatted.strip()

    return clean_text(data)

def generate_csv(data, file_path):
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(["File Name", "Summary"])

        for item in data:
            file_name = clean_text(item["file"])
            formatted_summary = format_summary(item["summary"])
            writer.writerow([file_name, formatted_summary])