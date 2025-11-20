# @Maaitrayo Das, 19 Nov 2025

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, HTTPException
from scripts.build_kb_index_embeddings import build_index, KB_EMB_PATH

from agent.orchestrator import triage_ticket
from app.schema import TriageRequest, TriageResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Check if embeddings exist
    if not KB_EMB_PATH.exists():
        print(f"Embeddings not found at {KB_EMB_PATH}. Generating...")
        build_index()
    else:
        print(f"Embeddings found at {KB_EMB_PATH}.")
    yield
    # Shutdown: (nothing to do)


app = FastAPI(title="Support Ticket Triage Agent", lifespan=lifespan)


@app.post("/triage", response_model=TriageResponse)
def triage_endpoint(payload: TriageRequest):
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description must not be empty.")

    result = triage_ticket(description)
    return TriageResponse(**result)