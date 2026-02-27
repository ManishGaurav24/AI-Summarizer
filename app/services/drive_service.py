# drive_service.py

import io
import os
import re
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import Flow

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

REDIRECT_URI = "http://127.0.0.1:8000/auth/callback"


# ---------------------------------------
# Create OAuth Flow (Web-based)
# ---------------------------------------
def create_flow():
    flow = Flow.from_client_secrets_file(
        "credentials.json",
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    return flow


# ---------------------------------------
# Build Drive Service
# ---------------------------------------
def get_drive_service(credentials):
    return build("drive", "v3", credentials=credentials)


def get_folder_name(service, folder_id):
    folder = service.files().get(
        fileId=folder_id,
        fields="id, name"
    ).execute()

    folder_name = folder.get("name", "default_folder")
    # Replace anything except letters, numbers, underscore, hyphen with _
    safe_folder_name = re.sub(r'[^a-zA-Z0-9_-]', '_', folder_name)
    return safe_folder_name
# ---------------------------------------
# List Files in Folder
# ---------------------------------------
def list_files(service, folder_id):
    query = f"'{folder_id}' in parents and mimeType != 'application/vnd.google-apps.folder'"

    results = service.files().list(
        q=query,
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])

    print("Drive returned files:", files)

    return files


# ---------------------------------------
# Download File
# ---------------------------------------
def download_file(service, file_id, file_name, folder_name):
    os.makedirs(os.path.join("temp", folder_name), exist_ok=True)

    request = service.files().get_media(fileId=file_id)
    file_path = os.path.join("temp", folder_name, file_name)

    with io.FileIO(file_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False

        while not done:
            status, done = downloader.next_chunk()

    return file_path