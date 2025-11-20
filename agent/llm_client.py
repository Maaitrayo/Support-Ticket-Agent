import os
from typing import Dict
from dotenv import load_dotenv
from openai import AsyncOpenAI
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAIError
import asyncio

load_dotenv()

class LLMClientMock:
    """
    Simple LLM wrapper.
    Currently uses a rule-based 'mock' for classification and summary
    """

    def __init__(self) -> None:
        self.use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    async def classify_ticket(self, description: str) -> Dict[str, str]:
        """
        Return a dict with:
        {
          "summary": str,
          "category": str,
          "severity": str
        }
        """
        if self.use_mock:
            return await self._mock_classify(description)
        else:
            return await self._mock_classify(description)

    async def _mock_classify(self, description: str) -> Dict[str, str]:
        """
        Simple rule-based classification and summary generation.
        """
        # Simulate small network delay for realism in mock mode if desired, 
        # but for now we just keep it fast or add a tiny sleep.
        # await asyncio.sleep(0.1) 
        
        text = description.lower()

        # Summary: first sentence or first ~120 chars
        summary = description.strip()
        if len(summary) > 120:
            summary = summary[:117].rsplit(" ", 1)[0] + "..."

        # Category heuristic
        if any(w in text for w in ["charge", "billing", "invoice", "payment"]):
            category = "Billing"
        elif any(w in text for w in ["login", "signin", "sign-in", "password", "authentication"]):
            category = "Login"
        elif any(w in text for w in ["slow", "lag", "performance", "timeout"]):
            category = "Performance"
        elif any(w in text for w in ["how do i", "how to", "can i", "is it possible"]):
            category = "Question/How-To"
        elif any(w in text for w in ["crash", "error", "bug", "exception", "500", "404", "429"]):
            category = "Bug"
        else:
            category = "Other"

        # Severity heuristic
        if any(w in text for w in ["data loss", "security", "breach", "cannot access", "down", "unavailable"]):
            severity = "Critical"
        elif any(w in text for w in ["crash", "500", "not working", "fails", "error"]):
            severity = "High"
        elif any(w in text for w in ["slow", "sometimes", "intermittent", "occasionally"]):
            severity = "Medium"
        else:
            severity = "Low"

        return {
            "summary": summary,
            "category": category,
            "severity": severity,
        }


class LLMClient:
    """
    Wrapper for OpenAI + fallback mock
    """

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.client = None

        if self.api_key:
            self.client = AsyncOpenAI(api_key=self.api_key)
            self.use_mock = False
        else:
            self.use_mock = True

    async def classify_ticket(self, description: str) -> Dict[str, str]:
        return await self._openai_classify(description)
    

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(OpenAIError)
    )
    async def _openai_classify(self, description: str) -> Dict[str, str]:

        system_message = (
            "You are a support ticket triage assistant. "
            "You MUST respond with a single JSON object only, no explanation, no markdown."
        )

        user_message = f"""
        Extract the following information from the support ticket.

        Ticket: "{description}"

        Return ONLY a JSON object with exactly these keys:
        - summary: string, 1 sentence summary
        - category: one of ["Billing", "Login", "Performance", "Bug", "Question/How-To", "Other"]
        - severity: one of ["Low", "Medium", "High", "Critical"]
        """

        try:
            resp = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,
                response_format={"type": "json_object"},
            )

            content = resp.choices[0].message.content
            result = json.loads(content)
            return result
        except OpenAIError as e:
            print(f"OpenAI API Error: {e}")
            raise e
        except Exception as e:
            print("Failed to parse LLM response or other error, using mock fallback. Error:", e)
            return await LLMClientMock()._mock_classify(description)