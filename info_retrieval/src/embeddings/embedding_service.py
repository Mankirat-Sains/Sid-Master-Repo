from __future__ import annotations

import hashlib
from typing import List, Optional

import numpy as np

from ..utils.config import AppConfig
from ..utils.logger import get_logger

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

        if self._should_use_openai():
            return self._embed_batch_with_openai(cleaned_texts)
        if self._should_use_local_model():
            return [self._embed_with_local(t) for t in cleaned_texts]

        return [self._debug_embed(t) for t in cleaned_texts]

    def _should_use_openai(self) -> bool:
        return bool(self.config.openai_api_key) and not self.config.use_local_embeddings

    def _should_use_local_model(self) -> bool:
        return self.config.use_local_embeddings

    def _embed_with_openai(self, text: str) -> List[float]:
        client = self._get_openai_client()
        response = client.embeddings.create(model=self.model_name, input=text)
        return response.data[0].embedding

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
