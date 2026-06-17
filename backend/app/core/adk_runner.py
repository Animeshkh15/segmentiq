import json
import os

import yaml
from dotenv import load_dotenv
from google import genai

from app.schemas.schemas import AgentResult

load_dotenv()


class ADKRunner:

    def __init__(self):

        with open(
            "config/config.yaml",
            "r",
            encoding="utf-8"
        ) as file:

            self.config = yaml.safe_load(file)

        self.client = genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY")
        )

        self.model_name = self.config["model"]["model_name"]

        self.temperature = self.config["model"]["temperature"]

        self.system_prompt = self.config["prompt"]["system_prompt"]

    def classify_page(
        self,
        page_number: int,
        text: str
    ) -> AgentResult:
        import time
        import random

        max_retries = 5
        base_backoff = 4.0

        for attempt in range(max_retries):
            try:
                prompt = f"""
{self.system_prompt}

Page Content:

{text}
"""
                print(
                    f"Calling Gemini for page {page_number} (Attempt {attempt + 1}/{max_retries})"
                )

                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                print(
                    f"Gemini response received for page {page_number}"
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

                return AgentResult(
                    success=True,
                    category=result["category"],
                    reasoning=result["reasoning"]
                )

            except Exception as e:
                err_msg = str(e)
                print(
                    f"Gemini Error Page {page_number} (Attempt {attempt + 1}/{max_retries}): {err_msg}"
                )

                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
                    if attempt < max_retries - 1:
                        sleep_time = (base_backoff ** attempt) + random.uniform(0.5, 1.5)
                        print(f"Rate limit hit. Retrying page {page_number} in {sleep_time:.2f} seconds...")
                        time.sleep(sleep_time)
                        continue

                if attempt == max_retries - 1:
                    return AgentResult(
                        success=False,
                        error=err_msg
                    )
                time.sleep(1.0)