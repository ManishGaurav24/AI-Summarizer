import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GOOGLE_FOLDER_ID = os.getenv("GOOGLE_FOLDER_ID")

settings = Settings()