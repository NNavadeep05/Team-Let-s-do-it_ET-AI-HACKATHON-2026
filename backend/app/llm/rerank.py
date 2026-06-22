import logging
from typing import List
from FlagEmbedding import FlagReranker

logger = logging.getLogger(__name__)


class RerankerService:
    def __init__(self):
        self.reranker = None

    def _init_model(self):
        if self.reranker is None:
            try:
                logger.info("Initializing BAAI/bge-reranker-v2-m3 model...")
                # Download BAAI/bge-reranker-v2-m3 (local, runs on CPU/GPU depending on torch availability)
                # use_fp16=False is safer for default CPU fallback
                self.reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=False)
            except Exception as e:
                logger.error(f"Failed to load FlagReranker BAAI/bge-reranker-v2-m3: {e}")

    def compute_scores(self, query: str, passages: List[str]) -> List[float]:
        """
        Compute similarity scores for a list of passages against a query.
        Returns a list of float scores matching the passages order.
        Falls back to a token-overlap Jaccard score on failure.
        """
        if not passages:
            return []

        self._init_model()
        
        if self.reranker:
            try:
                pairs = [[query, p] for p in passages]
                scores = self.reranker.compute_score(pairs)
                if isinstance(scores, (int, float)):
                    return [float(scores)]
                return [float(s) for s in scores]
            except Exception as e:
                logger.error(f"Error executing FlagReranker: {e}")

        # Fallback simple Jaccard similarity score
        query_words = set(query.lower().split())
        scores = []
        for p in passages:
            p_words = set(p.lower().split())
            intersection = query_words.intersection(p_words)
            union = query_words.union(p_words)
            score = len(intersection) / len(union) if union else 0.0
            scores.append(score)
        return scores


reranker_service = RerankerService()
