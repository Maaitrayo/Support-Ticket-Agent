# @Maaitrayo Das, 19 Nov 2025

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple
import numpy as np
from openai import OpenAI

from .llm_client import LLMClientMock, LLMClient
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import OpenAIError


def _get_kb_path() -> Path:
    env_path = os.getenv("KB_PATH")
    if env_path:
        return Path(env_path)
    # default: ../kb/kb.json relative to this file
    return Path(__file__).resolve().parents[1] / "kb" / "kb.json"


def load_kb() -> List[Dict[str, Any]]:
    kb_path = _get_kb_path()
    with kb_path.open("r", encoding="utf-8") as f:
        return json.load(f)


KB_ENTRIES: List[Dict[str, Any]] = load_kb()
if os.getenv("MOCK_LLM", "true").lower() in ("1", "true", "yes"):
    llm_client = LLMClientMock()
else:
    llm_client = LLMClient()


def classify_ticket(description: str) -> Dict[str, str]:
    """
    Use LLM (mock / real) to extract summary, category, severity.
    """
    return llm_client.classify_ticket(description)


def _tokenize(text: str) -> List[str]:
    """
    A simple word tokenizer splitting on non-alphanumeric characters.
    Example: 
        "Login error 500!" -> ["login", "error", "500"]
        "Checkout error 500 on mobile" -> ["checkout", "error", "500", "on", "mobile"]
    """
    import re

    return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t]


def search_kb_mock(query: str, top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Very simple keyword-based similarity search over KB.
    Scores by overlapping tokens between query and (title + symptoms).
    Returns top_n entries with an added "match_score" field.
    Example:
        query_tokens = {"checkout", "keeps", "failing", "with", "error", "500", "on", "mobile", "when", "i", "try", "to", "pay"}
        entry_tokens = {"checkout", "error", "500", "on", "mobile", "payment"}
        overlap = query_tokens & entry_tokens = {"checkout", "error", "500", "on", "mobile"}
        score = len(overlap) / len(entry_tokens) = 5 / 6 ~ 0.83
    """
    query_tokens = set(_tokenize(query))
    scored: List[Tuple[float, Dict[str, Any]]] = []

    for entry in KB_ENTRIES:
        text = entry["title"] + " " + " ".join(entry.get("symptoms", []))
        entry_tokens = set(_tokenize(text))
        overlap = query_tokens & entry_tokens
        if not entry_tokens:
            score = 0.0
        else:
            score = len(overlap) / len(entry_tokens)
        scored.append((score, entry))

    scored.sort(key=lambda x: x[0], reverse=True)
    top_entries: List[Dict[str, Any]] = []
    for score, entry in scored[:top_n]:
        e = dict(entry)
        e["match_score"] = round(float(score), 3)
        top_entries.append(e)

    return top_entries

# -----------------
# KB Embedding-based search
# -----------------

client = OpenAI()
EMB_MODEL = "text-embedding-3-small"

def load_kb_index():
    path = Path(__file__).resolve().parents[1] / "kb" / "kb_index_embeddings.json"
    with path.open("r") as f:
        return json.load(f)

KB_EMB_INDEX = None

def get_kb_index():
    global KB_EMB_INDEX
    if KB_EMB_INDEX is None:
        KB_EMB_INDEX = load_kb_index()
    return KB_EMB_INDEX

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(OpenAIError)
)
def embed_query(query: str) -> list:
    try:
        return client.embeddings.create(model=EMB_MODEL, input=query).data[0].embedding
    except OpenAIError as e:
        print(f"OpenAI API Error during embedding: {e}")
        raise e

def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_kb_embeddings(query: str, top_n: int = 3):
    q_emb = embed_query(query)
    scored = []
    
    kb_index = get_kb_index()

    for item in kb_index:
        score = cosine(np.array(q_emb), np.array(item["embedding"]))
        kb_entry = next(e for e in KB_ENTRIES if e["id"] == item["id"])
        scored.append((float(score), kb_entry))

    scored.sort(key=lambda x: x[0], reverse=True)

    top = []
    for score, entry in scored[:top_n]:
        e = dict(entry)
        e["match_score"] = round(score, 3)
        top.append(e)

    return top

def decide_next_action(
    ticket_meta: Dict[str, str], kb_matches: List[Dict[str, Any]]
) -> Tuple[bool, str]:
    """
    Decide:
    - Is it a known issue?
    - What next action should support take?
    """
    severity = ticket_meta["severity"]
    category = ticket_meta["category"]
    summary = ticket_meta["summary"]

    top_score = kb_matches[0]["match_score"] if kb_matches else 0.0
    known_issue = top_score >= 0.3 and bool(kb_matches)

    if known_issue:
        top_issue = kb_matches[0]
        issue_id = top_issue["id"]
        rec = top_issue.get("recommended_action", "")
        next_action = (
            f"Likely known issue ({issue_id}: {top_issue['title']}). "
            f"Attach this KB entry and respond to the user. "
            f"Recommended internal action: {rec}"
        )
        return True, next_action

    # New issues: pick sensible default based on category and severity
    if severity in ("High", "Critical"):
        next_action = (
            f"Likely new {category} issue with {severity} severity. "
            f"Escalate to the appropriate product/engineering team and gather logs, "
            f"screenshots, and reproduction steps from the customer."
        )
    elif category in ("Question/How-To", "Question"):
        next_action = (
            "Likely new question/how-to. "
            "Search help center; if no article exists, answer directly and consider creating a new KB article."
        )
    else:
        next_action = (
            f"Likely new {category} issue with {severity} severity. "
            "Ask customer for more details (screenshots, timestamps, steps to reproduce) "
            "and create a new ticket for engineering if impact is confirmed."
        )

    return False, next_action
