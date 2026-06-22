import logging
from typing import List
from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingsService:
    def __init__(self):
        self.openai_available = bool(settings.OPENAI_API_KEY)
        if self.openai_available:
            self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            logger.warning("OPENAI_API_KEY not configured. Falling back to local fastembed for embeddings.")
            from fastembed import TextEmbedding
            # This downloads a small local model on first run
            self.local_model = TextEmbedding()

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Embed a list of texts using OpenAI text-embedding-3-large (3072-d).
        Falls back to local fastembed (zero-padded to 3072-d) if key is missing or on error.
        """
        if not texts:
            return []

        if self.openai_available:
            try:
                response = await self.client.embeddings.create(
                    input=texts,
                    model=settings.EMBED_MODEL
                )
                return [e.embedding for e in response.data]
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}. Falling back to local fastembed...")

        # Local fallback
        embeddings = list(self.local_model.embed(texts))
        result = []
        for emb in embeddings:
            vector = list(emb)
            # OpenAI text-embedding-3-large is 3072 dimensions.
            # Local models are typically 384 or 768. We pad to 3072.
            if len(vector) < 3072:
                vector = vector + [0.0] * (3072 - len(vector))
            elif len(vector) > 3072:
                vector = vector[:3072]
            result.append(vector)
        return result


embeddings_service = EmbeddingsService()
