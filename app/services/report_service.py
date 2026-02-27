import csv

def generate_csv(data, file_path):
    with open(file_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["File Name", "Summary"])

        for item in data:
            writer.writerow([item["file"], item["summary"]])