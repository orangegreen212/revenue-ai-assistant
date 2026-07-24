"""Embeddings factory — shared by ingest.py and rag/rag_core.py so both use
the exact same embedding model/backend (mismatched embeddings between
ingest-time and query-time would silently break retrieval).

Uses the HuggingFace Inference API (remote call) instead of loading the
model locally via sentence-transformers/torch. This keeps the backend's
memory footprint small enough for free-tier hosting (Render's 512MB limit) —
loading torch + transformers locally can use 500MB+ RAM on its own.

Requires HF_TOKEN (a free "Read" token from huggingface.co/settings/tokens).
"""

import os

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_embeddings():
    from langchain_huggingface import HuggingFaceEndpointEmbeddings

    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError(
            "HF_TOKEN is not set. Create a free 'Read' token at "
            "huggingface.co/settings/tokens and add it to your .env."
        )

    return HuggingFaceEndpointEmbeddings(
        model=EMBEDDING_MODEL,
        task="feature-extraction",
        huggingfacehub_api_token=token,
    )
