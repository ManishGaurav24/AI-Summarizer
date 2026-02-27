# summarizer_service.py

import time
import random
import re
from google import genai
from app.core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

MAX_RETRIES = 5
BASE_DELAY = 2


def summarize_text(text: str):

    prompt = f"""
    You are a professional document summarizer.

    Summarize the following document into 5–8 short bullet points.

    Rules:
    - Each point must be 1 sentence only.
    - Each point must be concise (max 20 words).
    - Use clear business language.
    - Do NOT write paragraphs.
    - Return output strictly in this format:

    - Point one
    - Point two
    - Point three

    Document:
    {text[:15000]}
    """

    for attempt in range(MAX_RETRIES):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )

            print("Gemini response received.")

            summary_text = response.text.strip()

            # Convert bullet lines into clean list items
            lines = [
                line.strip().lstrip("-• ").strip()
                for line in summary_text.split("\n")
                if line.strip()
            ]

            return lines

        except Exception as e:
            error_str = str(e)
            print(f"Gemini Error (Attempt {attempt+1}):", error_str)

            # Retry only for rate-limit / quota errors
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:

                if attempt < MAX_RETRIES - 1:

                    # Try to extract retryDelay from Gemini response
                    retry_match = re.search(r"retryDelay': '(\d+)s'", error_str)

                    if retry_match:
                        sleep_time = int(retry_match.group(1))
                    else:
                        # Exponential backoff with jitter
                        sleep_time = BASE_DELAY * (2 ** attempt)
                        sleep_time += random.uniform(0, 1)

                    print(f"Rate limit hit. Sleeping {sleep_time:.2f} seconds before retry...")
                    time.sleep(sleep_time)

                else:
                    print("Max retries exceeded due to quota.")
                    return "Summary failed due to quota limit."

            else:
                # If it's not a rate-limit issue, don't retry
                return f"Summary failed: {error_str}"

    return "Summary failed."