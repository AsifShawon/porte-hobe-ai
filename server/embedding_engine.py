"""Embedding helpers and storage/search utilities for Supabase + pgvector.

Notes
-----
- Uses local Ollama with embeddinggemma model for embeddings
- Falls back to deterministic mock if Ollama is unavailable
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Iterable, List, Optional, Tuple, Dict, Any

import numpy as np
import ollama

from config import supabase

logger = logging.getLogger(__name__)

# EmbeddingGemma produces 768-dimensional embeddings
EMBED_DIM = 768
EMBEDDING_MODEL = "embeddinggemma:latest"


def _deterministic_vec(text: str, dim: int = EMBED_DIM) -> List[float]:
    """Create a deterministic pseudo-embedding from text using SHA256.

    This is only for development when real embeddings aren't available.
    """
    h = hashlib.sha256(text.encode("utf-8")).digest()
    # Repeat the hash to fill the vector; normalize to unit length
    vals = np.frombuffer(h * ((dim // len(h)) + 1), dtype=np.uint8)[:dim].astype(np.float32)
    vec = vals / (np.linalg.norm(vals) + 1e-8)
    return vec.tolist()


def chunk_text(text: str, max_tokens: int = 500) -> List[str]:
    """Simple chunking by sentence/length; can be replaced with token-aware logic."""
    text = text.strip()
    if not text:
        return []
    chunks: List[str] = []
    current: List[str] = []
    count = 0
    for part in text.split():
        current.append(part)
        count += 1
        if count >= max_tokens:
            chunks.append(" ".join(current))
            current, count = [], 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def embed_text(texts: Iterable[str]) -> List[List[float]]:
    """Embed a batch of texts using Ollama embeddinggemma model.

    Falls back to deterministic mock if Ollama is unavailable.
    """
    texts_list = list(texts)
    if not texts_list:
        return []

    try:
        # Use Ollama embeddinggemma for embeddings
        embeddings = []
        for text in texts_list:
            response = ollama.embeddings(
                model=EMBEDDING_MODEL,
                prompt=text
            )
            embeddings.append(response['embedding'])

        logger.debug(f"Generated {len(embeddings)} embeddings using {EMBEDDING_MODEL}")
        return embeddings

    except Exception as e:
        logger.warning(f"Ollama embedding failed: {e}. Falling back to deterministic embedding.")
        # Fallback to deterministic embedding
        return [_deterministic_vec(t) for t in texts_list]


def store_user_memory(user_id: str, query: str, response: str, summary: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create an embedding of the summary and insert into user_memory."""
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    emb = embed_text([summary])[0]
    payload = {
        "user_id": user_id,
        "query": query,
        "response": response,
        "summary": summary,
        "embedding": emb,
        "metadata": metadata or {},
    }
    res = supabase.table("user_memory").insert(payload).execute()
    return res.data[0] if res.data else {}


def store_universal_memory(query: str, content: str, source: Optional[str] = None, url: Optional[str] = None, tags: Optional[List[str]] = None) -> Dict[str, Any]:
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    emb = embed_text([content])[0]
    payload = {
        "query": query,
        "content": content,
        "embedding": emb,
        "source": source,
        "url": url,
        "tags": tags or [],
    }
    res = supabase.table("universal_memory").insert(payload).execute()
    return res.data[0] if res.data else {}


def search_user_memory(user_id: str, text: str, k: int = 5) -> List[Dict[str, Any]]:
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    emb = embed_text([text])[0]
    # Call the RPC defined in migrations/002_functions.sql
    res = supabase.rpc("match_user_memory", {"p_user_id": user_id, "query_embedding": emb, "match_count": k}).execute()
    return res.data or []


def search_universal_memory(text: str, k: int = 5) -> List[Dict[str, Any]]:
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    emb = embed_text([text])[0]
    res = supabase.rpc("match_universal_memory", {"query_embedding": emb, "match_count": k}).execute()
    return res.data or []


def search_notes(user_id: str, text: str, k: int = 5) -> List[Dict[str, Any]]:
    if supabase is None:
        raise RuntimeError("Supabase client not configured")
    emb = embed_text([text])[0]
    res = supabase.rpc("match_notes", {"p_user_id": user_id, "query_embedding": emb, "match_count": k}).execute()
    return res.data or []
