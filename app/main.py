# main.py
import os
from datetime import datetime
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.services.drive_service import (
    create_flow,
    get_drive_service,
    list_files,
    download_file,
    get_folder_name
)
from app.services.parser_service import extract_text
from app.services.summarizer_service import summarize_text
from app.services.report_service import generate_csv
from concurrent.futures import ThreadPoolExecutor, as_completed

app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

os.makedirs("temp", exist_ok=True)
os.makedirs("output", exist_ok=True)

# Temporary in-memory credential store
credentials_store = {}

def process_single_file(credentials, file, folder_name):
    service = get_drive_service(credentials)
    if not file["name"].lower().endswith((".pdf", ".docx", ".txt")):
        return None

    path = download_file(service, file["id"], file["name"], folder_name)
    text = extract_text(path)

    if not text.strip():
        return None

    summary = summarize_text(text)

    return {
        "file": file["name"],
        "summary": summary
    }
# ---------------------------------------
# Step 1: Redirect user to Google Login
# ---------------------------------------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "summaries": None
    })

@app.get("/login")
def login():
    flow = create_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true"
    )

    credentials_store["state"] = state
    return RedirectResponse(authorization_url)


# ---------------------------------------
# Step 2: Google redirects back here
# ---------------------------------------
@app.get("/auth/callback")
def auth_callback(request: Request):
    flow = create_flow()

    flow.fetch_token(authorization_response=str(request.url))

    credentials = flow.credentials
    credentials_store["creds"] = credentials

    return RedirectResponse("/process")


# ---------------------------------------
# Step 3: Process Drive Files
# ---------------------------------------
@app.get("/process", response_class=HTMLResponse)
def process_documents(request: Request):
    credentials = credentials_store.get("creds")

    if not credentials:
        return RedirectResponse("/")

    service = get_drive_service(credentials)
    files = list_files(service, settings.GOOGLE_FOLDER_ID)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "files": files,
        "summaries": None
    })

@app.get("/summarize", response_class=HTMLResponse)
def summarize_documents(request: Request):
    credentials = credentials_store.get("creds")

    if not credentials:
        return RedirectResponse("/")

    service = get_drive_service(credentials)
    files = list_files(service, settings.GOOGLE_FOLDER_ID)

    # Get actual folder name from Drive
    folder_name = get_folder_name(service, settings.GOOGLE_FOLDER_ID)

    summaries = []

    with ThreadPoolExecutor(max_workers=min(3, len(files))) as executor:
        futures = [
            executor.submit(process_single_file, credentials, file, folder_name)
            for file in files
        ]

        for future in as_completed(futures):
            result = future.result()
            if result:
                summaries.append(result)

    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Summary_{folder_name}_{timestamp}.csv"
    output_path = os.path.join("output", filename)
    generate_csv(summaries, output_path)

    return templates.TemplateResponse("index.html", {
        "request": request,
        "files": files,
        "summaries": summaries
    })


# ---------------------------------------
# Step 4: Download CSV
# ---------------------------------------
@app.get("/download")
def download_csv():
    return FileResponse("summaries.csv", filename="summaries.csv")