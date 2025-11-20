"""
@Maaitrayo Das, 19 Nov 2025
run: python -m pytest
"""

import json
import types

import agent.llm_client as llm_mod
from agent.llm_client import LLMClient


class DummyChoiceMessage:
    def __init__(self, content: str):
        self.content = content


class DummyChoice:
    def __init__(self, content: str):
        self.message = DummyChoiceMessage(content)


class DummyOpenAIResponse:
    def __init__(self, content: str):
        self.choices = [DummyChoice(content)]


class DummyChatCompletions:
    def __init__(self, content: str):
        self._content = content

    def create(self, model, messages, temperature):
        # Ignore parameters, just return dummy response
        return DummyOpenAIResponse(self._content)


class DummyOpenAIClient:
    def __init__(self, content: str):
        # Mimic structure: client.chat.completions.create(...)
        self.chat = types.SimpleNamespace(
            completions=DummyChatCompletions(content)
        )


def test_classify_ticket_parses_valid_json(monkeypatch):
    """
    When OpenAI returns valid JSON, LLMClient should parse and return it.
    """
    # Ensure OPENAI_API_KEY exists so LLMClient sets up `client`
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # Build a deterministic JSON response string
    fake_json = json.dumps(
        {
            "summary": "User cannot login.",
            "category": "Login",
            "severity": "High",
        }
    )

    client = LLMClient()
    # Replace real OpenAI client with our dummy
    client.client = DummyOpenAIClient(content=fake_json)

    description = "I cannot login even though my password is correct."
    result = client.classify_ticket(description)

    assert result["summary"] == "User cannot login."
    assert result["category"] == "Login"
    assert result["severity"] == "High"


def test_classify_ticket_falls_back_on_invalid_json(monkeypatch):
    """
    When the model returns invalid JSON, LLMClient should use LLMClientMock()._mock_classify().
    """
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    # OpenAI returns invalid JSON here
    invalid_content = "this is not valid json"

    client = LLMClient()
    client.client = DummyOpenAIClient(content=invalid_content)

    # Create a dummy LLMClientMock to verify fallback was used
    class DummyLLMClientMock:
        def __init__(self):
            self.called_with = None

        def _mock_classify(self, description: str):
            self.called_with = description
            return {
                "summary": "fallback summary",
                "category": "Other",
                "severity": "Low",
            }

    dummy_mock = DummyLLMClientMock()

    # Patch LLMClientMock in the module to return our dummy
    monkeypatch.setattr(llm_mod, "LLMClientMock", lambda: dummy_mock)

    description = "Some description that causes invalid JSON."
    result = client.classify_ticket(description)

    # Ensure the fallback result is returned
    assert result["summary"] == "fallback summary"
    assert result["category"] == "Other"
    assert result["severity"] == "Low"

    # Ensure our dummy mock was actually called with the description
    assert dummy_mock.called_with == description
