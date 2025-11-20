"""
@Maaitrayo Das, 19 Nov 2025
python -m scripts.build_kb_index_embeddings
"""

import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
client = OpenAI()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
KB_PATH = PROJECT_ROOT / "kb" / "kb.json"
KB_EMB_PATH = PROJECT_ROOT / "kb" / "kb_index_embeddings.json"

MODEL = "text-embedding-3-small"

def load_kb():
    with KB_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def embed(text: str):
    return client.embeddings.create(model=MODEL, input=text).data[0].embedding

def build_index():
    kb_entries = load_kb()
    index = []

    for entry in tqdm(kb_entries, desc="Embedding KB entries", unit="entry"):
        text = entry["title"] + " " + " ".join(entry.get("symptoms", []))
        try:
            emb = embed(text)
        except Exception as e:
            print(f"Warning: failed to embed entry id={entry.get('id')} title={entry.get('title')}: {e}")
            continue
        index.append({"id": entry["id"], "embedding": emb})

    with KB_EMB_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"Saved: {KB_EMB_PATH}")

if __name__ == "__main__":
    build_index()
