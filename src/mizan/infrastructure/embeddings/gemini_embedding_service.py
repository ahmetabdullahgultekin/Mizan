"""
Google Gemini Embedding API service.

Uses Google's Gemini Embedding 2 (or text-embedding-004) for high-quality
multimodal embeddings. Requires a Google Gemini API key.

Cost: Extremely low — embedding is much cheaper than text generation.
The entire Quran (~77k words) costs only a few cents or is free on the
generous Gemini API Studio free tier.
"""

from __future__ import annotations

import asyncio
from typing import Any

from mizan.domain.services.embedding_service import IEmbeddingService

# Gemini embedding model names
GEMINI_EMBEDDING_2 = "gemini-embedding-2-preview"
GEMINI_TEXT_EMBEDDING_004 = "text-embedding-004"


class GeminiEmbeddingService(IEmbeddingService):
    """
    Embedding service backed by Google Gemini Embedding API.

    Supports gemini-embedding-2-preview (multimodal) and
    text-embedding-004 (text-only, slightly cheaper).

    Note: Dimension for Gemini embeddings is 768 by default.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str = GEMINI_TEXT_EMBEDDING_004,
    ) -> None:
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when using Gemini embedding provider. "
                "Set GEMINI_API_KEY in your .env file."
            )
        self._api_key = api_key
        self._model_name = model_name
        self._client: Any = None

    def _get_client(self) -> Any:
        """Get or create the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
            except ImportError as exc:
                raise RuntimeError(
                    "google-generativeai is not installed. "
                    "Install with: pip install google-generativeai"
                ) from exc
            genai.configure(api_key=self._api_key)
            self._client = genai
        return self._client

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single text via Gemini API."""
        results = await self.embed_batch([text])
        return results[0]

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a batch of texts via Gemini API.

        Gemini API supports batch embedding to minimize round trips.
        """
        loop = asyncio.get_event_loop()

        def _embed() -> list[list[float]]:
            import google.generativeai as genai
            self._get_client()

            result = genai.embed_content(
                model=f"models/{self._model_name}",
                content=texts,
                task_type="RETRIEVAL_DOCUMENT",
            )
            return [list(emb) for emb in result["embedding"]]

        return await loop.run_in_executor(None, _embed)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def embedding_dimension(self) -> int:
        return 768


def get_gemini_embedding_service(
    api_key: str,
    model_name: str = GEMINI_TEXT_EMBEDDING_004,
) -> GeminiEmbeddingService:
    """Create a Gemini embedding service instance."""
    return GeminiEmbeddingService(api_key=api_key, model_name=model_name)
