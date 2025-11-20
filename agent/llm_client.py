# @Maaitrayo Das, 19 Nov 2025

import os
from typing import Dict


class LLMClientMock:
    """
    Simple LLM wrapper.
    Currently uses a rule-based 'mock' for classification and summary
    """

    def __init__(self) -> None:
        self.use_mock = os.getenv("USE_MOCK_LLM", "true").lower() == "true"

    def classify_ticket(self, description: str) -> Dict[str, str]:
        """
        Return a dict with:
        {
          "summary": str,
          "category": str,
          "severity": str
        }
        """
        if self.use_mock:
            return self._mock_classify(description)
        else:
            return self._mock_classify(description)

    def _mock_classify(self, description: str) -> Dict[str, str]:
        """
        Simple rule-based classification and summary generation.
        """
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
