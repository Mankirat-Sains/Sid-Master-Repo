from __future__ import annotations

import hashlib
import json
import os
from typing import List, Optional, Tuple

import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

from utils.config import AppConfig
from utils.logger import get_logger

try:
    import redis  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    redis = None

logger = get_logger(__name__)


class EmbeddingService:
    """
    Handles embedding generation via OpenAI, local transformers, or a deterministic fallback.
    """

    def __init__(self, config: AppConfig, model_name: Optional[str] = None) -> None:
        self.config = config
        self.model_name = model_name or config.embedding_model
        self._openai_client = None
        self._local_model = None
        self._fallback_dim = config.embedding_dim or 128
        self._redis = self._init_redis()

    def get_embedding_model(self) -> str:
        return self.model_name

    def embed_text(self, text: str) -> List[float]:
        text = text.strip()
        if not text:
            return []

        if self._should_use_openai():
            return self._embed_with_openai(text)
        if self._should_use_local_model():
            return self._embed_with_local(text)

        logger.warning("Falling back to deterministic embedding; configure OpenAI or a local model for production.")
        return self._debug_embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        cleaned_texts = [t.strip() for t in texts if t.strip()]
        if not cleaned_texts:
            return []

        cached_vectors, missing_texts, missing_indices = self._maybe_get_cached(cleaned_texts)

        if missing_texts:
            if self._should_use_openai():
                generated = self._embed_batch_with_openai(missing_texts)
            elif self._should_use_local_model():
                generated = [self._embed_with_local(t) for t in missing_texts]
            else:
                generated = [self._debug_embed(t) for t in missing_texts]
            self._cache_results(missing_texts, generated)
            for idx, vector in zip(missing_indices, generated):
                cached_vectors[idx] = vector

        return list(cached_vectors.values())

    def _should_use_openai(self) -> bool:
        return bool(self.config.openai_api_key) and not self.config.use_local_embeddings

    def _should_use_local_model(self) -> bool:
        return self.config.use_local_embeddings

    def _embed_with_openai(self, text: str) -> List[float]:
        client = self._get_openai_client()
        response = client.embeddings.create(model=self.model_name, input=text)
        return response.data[0].embedding

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def _embed_batch_with_openai(self, texts: List[str]) -> List[List[float]]:
        client = self._get_openai_client()
        response = client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]

    def _embed_with_local(self, text: str) -> List[float]:
        model = self._get_local_model()
        embedding = model.encode(text)
        if hasattr(embedding, "tolist"):
            return embedding.tolist()
        return list(embedding)

    def _get_openai_client(self):
        if self._openai_client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise ImportError("openai package is required for OpenAI embeddings") from exc

            self._openai_client = OpenAI(api_key=self.config.openai_api_key)
        return self._openai_client

    def _get_local_model(self):
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:  # pragma: no cover - environment dependent
                raise ImportError(
                    "sentence-transformers is required when USE_LOCAL_EMBEDDINGS=true"
                ) from exc

            self._local_model = SentenceTransformer(self.model_name)
        return self._local_model

    def _debug_embed(self, text: str) -> List[float]:
        """
        Deterministic embedding useful for tests and offline development.
        """
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:4], "big")
        rng = np.random.default_rng(seed)
        return rng.standard_normal(self._fallback_dim).astype(float).tolist()

    def _init_redis(self):
        url = os.getenv("REDIS_URL")
        if redis is None or not url:
            return None
        try:
            return redis.from_url(url)
        except Exception:
            return None

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]
        return f"embed:{self.model_name}:{digest}"

    def _maybe_get_cached(self, texts: List[str]) -> Tuple[Dict[int, List[float]], List[str], List[int]]:
        cached: Dict[int, List[float]] = {}
        missing_texts: List[str] = []
        missing_indices: List[int] = []
        if not self._redis:
            return {i: None for i in range(len(texts))}, texts, list(range(len(texts)))
        for idx, text in enumerate(texts):
            key = self._cache_key(text)
            try:
                cached_value = self._redis.get(key)
                if cached_value:
                    cached[idx] = json.loads(cached_value)
                    continue
            except Exception:
                pass
            missing_texts.append(text)
            missing_indices.append(idx)
            cached[idx] = None  # placeholder
        return cached, missing_texts, missing_indices

    def _cache_results(self, texts: List[str], embeddings: List[List[float]]) -> None:
        if not self._redis:
            return
        for text, vector in zip(texts, embeddings):
            key = self._cache_key(text)
            try:
                self._redis.setex(key, int(os.getenv("EMBEDDING_CACHE_TTL", 2592000)), json.dumps(vector))
            except Exception:
                continue
