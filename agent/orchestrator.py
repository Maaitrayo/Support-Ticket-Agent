# @Maaitrayo Das, 19 Nov 2025

import os
from typing import Any, Dict, List
from dotenv import load_dotenv

from .tools import classify_ticket, search_kb_mock, search_kb_embeddings, decide_next_action

load_dotenv()

def triage_ticket(description: str) -> Dict[str, Any]:
    """
    Main agent orchestration:
    1. Classify ticket (summary, category, severity)
    2. Search KB for related issues
    3. Decide known/new issue and next action
    """
    ticket_meta = classify_ticket(description)
    if os.getenv("MOCK_LLM", "true").lower() in ("1", "true", "yes"):
        kb_matches = search_kb_mock(description, top_n=3)
    else:
        kb_matches = search_kb_embeddings(description, top_n=3)
    known_issue, next_action = decide_next_action(ticket_meta, kb_matches)

    # Only expose a subset of KB fields externally
    related_issues: List[Dict[str, Any]] = [
        {
            "id": e["id"],
            "title": e["title"],
            "category": e["category"],
            "match_score": e["match_score"],
        }
        for e in kb_matches
    ]

    return {
        "summary": ticket_meta["summary"],
        "category": ticket_meta["category"],
        "severity": ticket_meta["severity"],
        "known_issue": known_issue,
        "related_issues": related_issues,
        "next_action": next_action,
    }
