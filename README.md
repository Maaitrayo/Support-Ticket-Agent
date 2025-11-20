# Support Ticket Triage Agent

An AI-powered agent designed to triage support tickets by understanding the ticket description, searching a Knowledge Base (KB), and proposing the next best action. This project exposes its functionality via a FastAPI HTTP service.

## Features

-   **Ticket Classification**: Analyzes ticket descriptions to extract a summary, category, and severity level.
-   **Knowledge Base Search**: Finds relevant past issues using either keyword matching (Mock mode) or semantic search (Embeddings mode).
-   **Action Recommendation**: Decides whether a ticket is a known issue or a new one and suggests the appropriate next step for support staff.
-   **REST API**: Provides a simple `/triage` endpoint for integration.

## Agent Design

### How the LLM is used
The agent leverages the LLM (or a deterministic mock) for two main purposes:
1.  **Classification**: The raw ticket description is processed to extract structured metadata: a concise **summary**, a broad **category** (e.g., Login, Billing), and a **severity** level.
2.  **Semantic Search**: In "Real Mode", the LLM generates vector embeddings for the ticket description, enabling the system to find semantically similar past issues in the Knowledge Base, even if the keywords don't match exactly.

### Tool Execution & KB Search
The `orchestrator.py` manages the flow:
1.  **Classify**: The ticket is first classified to understand its nature.
2.  **Search**: The agent searches the KB.
    -   *Mock Mode*: Uses token overlap (Jaccard similarity) to find matches.
    -   *Real Mode*: Uses Cosine similarity on vector embeddings.
3.  **Decide**: A heuristic-based decision engine (`decide_next_action`) compares the ticket against the search results. If a high-confidence match is found (> 0.3 score), it links the known issue. Otherwise, it uses the category and severity to propose a sensible default action (e.g., "Escalate to Engineering").

### Trade-offs
-   **Vector DB**: For simplicity and portability, this project uses in-memory NumPy arrays for vector search instead of a dedicated Vector Database (like Pinecone or Qdrant). This is sufficient for small datasets but would need scaling for production.
-   **Context Window**: The agent is currently stateless per request. It does not maintain a conversation history, which simplifies the architecture but limits the ability to ask follow-up questions dynamically.
-   **Mock Mode**: To facilitate rapid development and testing without incurring API costs, a robust "Mock Mode" was implemented. It trades off the semantic understanding of an LLM for deterministic, keyword-based logic.

## Project Structure

```
.
├── agent/                  # Core agent logic
│   ├── orchestrator.py     # Main triage workflow
│   ├── tools.py            # Tools for classification, search, and decision making
│   └── llm_client.py       # Interface for LLM interactions (Mock & Real)
├── app/                    # FastAPI application
│   ├── main.py             # API entry point and routes
│   └── schema.py           # Pydantic models for API requests/responses
├── kb/                     # Knowledge Base data
│   ├── kb.json             # JSON database of past tickets
│   └── kb_index_embeddings.json # Pre-computed embeddings for semantic search
├── scripts/                # Utility scripts
│   ├── build_kb_index_embeddings.py # Script to generate embeddings
│   └── ping_triage.sh      # Helper script to test the API
├── tests/                  # Test suite
├── .env.example            # Example environment variables
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## Prerequisites

-   Python 3.9+
-   [OpenAI API Key](https://platform.openai.com/) (if using real LLM features)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd Support-Ticket-Agent
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

1.  Copy `.env.example` to `.env`:
    ```bash
    cp .env.example .env
    ```

2.  Edit `.env` to configure the agent:

    -   `OPENAI_API_KEY`: Your OpenAI API key (required for embeddings and real LLM calls).
    -   `MOCK_LLM`: Controls the logic used for classification and search.
        -   `true`: Uses **Mock Mode**. Relies on simple keyword matching and deterministic logic ("maths logic"). No API costs.
        -   `false`: Uses **Real Mode**. Uses OpenAI's LLM for classification and semantic search (Embeddings). Requires `OPENAI_API_KEY`.
    -   `KB_PATH`: (Optional) Path to your custom KB JSON file.

## Usage

### Running the Server

Start the FastAPI server using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### Embeddings Generation

The application relies on a pre-computed embeddings index (`kb/kb_index_embeddings.json`) for semantic search (when `MOCK_LLM=false`).

-   **Automatic Generation**: When the server starts, it checks if the embeddings file exists. If not, it automatically generates it using the `kb.json` data.
-   **Manual Generation**: You can explicitly generate (or regenerate) the embeddings by running:
    ```bash
    python -m scripts.build_kb_index_embeddings
    ```
    *Note: This requires a valid `OPENAI_API_KEY`.*

### API Documentation

FastAPI automatically generates interactive API docs:
-   **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
-   **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Triage a Ticket

You can send a POST request to the `/triage` endpoint.

**Example using `curl`:**

```bash
curl -X POST "http://127.0.0.1:8000/triage" \
     -H "Content-Type: application/json" \
     -d '{"description": "I cannot login to my account, getting error 500"}'
```

**Example Response:**

```json
{
  "summary": "Login failure with error 500",
  "category": "Authentication",
  "severity": "High",
  "known_issue": true,
  "related_issues": [
    {
      "id": "TKT-101",
      "title": "Login 500 Error on Auth Service",
      "category": "Authentication",
      "match_score": 0.85
    }
  ],
  "next_action": "Likely known issue (TKT-101: Login 500 Error on Auth Service). Attach this KB entry and respond to the user. Recommended internal action: Restart Auth Service."
}
```

### Using the Helper Script

A shell script is provided to quickly test the endpoint:

```bash
./scripts/ping_triage.sh
```

## Testing

Run the test suite using `pytest`:

```bash
pytest
```
