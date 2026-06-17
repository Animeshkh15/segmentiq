import json
import os
import yaml
import time
import random
from dotenv import load_dotenv
from google import genai

load_dotenv()


class BoundaryDetector:

    def __init__(self):
        with open("config/config.yaml", "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        self.client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY")
        )
        self.model_name = self.config["model"]["model_name"]

    def detect_boundary(
        self,
        page_number: int,
        text: str,
        prev_page_number: int,
        prev_text: str,
        category: str
    ) -> dict:
        """
        Uses Gemini to determine if page_number starts a new document
        relative to prev_page_number, given both are classified under the same category.
        Returns:
            dict: { "is_boundary": bool, "reasoning": str }
        """
        max_retries = 5
        base_backoff = 4.0

        prompt = f"""You are an expert document analysis system.
We have two consecutive pages from a scanned document package. Both pages have been classified under the category: '{category}'.
Your task is to determine whether Page {page_number} starts a NEW independent document (e.g., a new invoice, new medical report, etc.) or if it is a continuation of the same document from Page {prev_page_number}.

Look for indicators that Page {page_number} starts a new document:
- Page number resets (e.g., Page {page_number} starts with "Page 1" or "Page 1 of X", or lists a page number of 1).
- Distinct document headers, titles, or letterheads on Page {page_number}.
- Changes in metadata like Vendor/Customer names, Patient names, Account Numbers, Invoice Numbers, or transaction dates.
- Previous page Page {prev_page_number} ending with closing elements (like "Total Due", "Signatures", "Page End") that indicate the previous document is completed.

Page {prev_page_number} Text:
---
{prev_text}
---

Page {page_number} Text:
---
{text}
---

Return a JSON object only in the following format:
{{
  "is_boundary": true or false,
  "reasoning": "<brief explanation why it is or is not a boundary, max 2 sentences>"
}}
"""

        for attempt in range(max_retries):
            try:
                print(
                    f"Calling Gemini for boundary detection on Page {page_number} (Attempt {attempt + 1}/{max_retries})"
                )
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                print(
                    f"Gemini boundary response received for Page {page_number}"
                )

                resp_text = response.text.strip()
                if resp_text.startswith("```json"):
                    resp_text = resp_text[7:]
                if resp_text.startswith("```"):
                    resp_text = resp_text[3:]
                if resp_text.endswith("```"):
                    resp_text = resp_text[:-3]
                resp_text = resp_text.strip()

                result = json.loads(resp_text)
                return {
                    "is_boundary": bool(result.get("is_boundary", False)),
                    "reasoning": str(result.get("reasoning", ""))
                }

            except Exception as e:
                err_msg = str(e)
                print(
                    f"Gemini Boundary Error Page {page_number} (Attempt {attempt + 1}/{max_retries}): {err_msg}"
                )

                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    if attempt < max_retries - 1:
                        sleep_time = (base_backoff ** attempt) + random.uniform(0.5, 1.5)
                        print(f"Rate limit hit. Retrying boundary check on Page {page_number} in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue

                if attempt == max_retries - 1:
                    # Default to False on failure to avoid accidental partitioning
                    return {
                        "is_boundary": False,
                        "reasoning": f"Failed to detect boundary due to Gemini error: {err_msg}"
                    }
                time.sleep(1.0)
