# @Maaitrayo Das, 19 Nov 2025

from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from scripts.build_kb_index_embeddings import build_index, KB_EMB_PATH
from app.config import settings
import time
from collections import defaultdict

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

# Simple in-memory rate limiter
request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    client_ip = request.client.host
    now = time.time()
    
    # Clean up old requests
    request_counts[client_ip] = [t for t in request_counts[client_ip] if now - t < settings.RATE_LIMIT_WINDOW_SECONDS]
    
    if len(request_counts[client_ip]) >= settings.RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "Rate limit exceeded. Please try again later."}
        )
    
    request_counts[client_ip].append(now)
    response = await call_next(request)
    return response

# Mount static files for UI
app.mount("/ui", StaticFiles(directory="app/static", html=True), name="static")

@app.get("/")
async def root():
    return {"message": "Support Ticket Agent API. Visit /ui for the interface."}


@app.post("/triage", response_model=TriageResponse)
def triage_endpoint(payload: TriageRequest):
    description = payload.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description must not be empty.")

    result = triage_ticket(description)
    return TriageResponse(**result)