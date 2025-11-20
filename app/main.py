# @Maaitrayo Das, 19 Nov 2025

from fastapi import FastAPI, HTTPException

from agent.orchestrator import triage_ticket
from app.schema import TriageRequest, TriageResponse


app = FastAPI(title="Support Ticket Triage Agent")


@app.post("/triage", response_model=TriageResponse)
def triage_endpoint(payload: TriageRequest):
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description must not be empty.")

    result = triage_ticket(description)
    return TriageResponse(**result)