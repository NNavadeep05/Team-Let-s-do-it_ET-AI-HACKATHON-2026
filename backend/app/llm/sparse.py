import logging
from typing import List, Dict, Any
from fastembed import SparseTextEmbedding

logger = logging.getLogger(__name__)


class SparseEmbeddingService:
    def __init__(self):
        self.model = None

    def _init_model(self):
        if self.model is None:
            try:
                logger.info("Initializing fastembed SPLADE model (prithivida/Splade_PP_en_v1)...")
                self.model = SparseTextEmbedding(model_name="prithivida/Splade_PP_en_v1")
            except Exception as e:
                logger.error(f"Failed to load fastembed SparseTextEmbedding prithivida/Splade_PP_en_v1: {e}")

    def encode(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Encode a list of texts into sparse vectors (indices and values).
        Returns a list of dicts: [{"indices": [...], "values": [...]}, ...]
        Falls back to a bag-of-words hash sparse vector on failure.
        """
        if not texts:
            return []

        self._init_model()

        if self.model:
            try:
                embeddings = list(self.model.embed(texts))
                return [
                    {
                        "indices": [int(i) for i in e.indices],
                        "values": [float(v) for v in e.values]
                    }
                    for e in embeddings
                ]
            except Exception as e:
                logger.error(f"Error executing SparseTextEmbedding: {e}")

        # Fallback simple hash-based bag of words
        results = []
        for text in texts:
            words = text.lower().split()
            word_counts = {}
            for w in words:
                word_counts[w] = word_counts.get(w, 0) + 1
            
            indices = []
            values = []
            for w, count in word_counts.items():
                # Hash word to an index between 0 and 100000
                idx = abs(hash(w)) % 100000
                indices.append(idx)
                values.append(float(count))
            
            # Sort by indices (Qdrant requires sorted sparse vector indices)
            sorted_pairs = sorted(zip(indices, values))
            if sorted_pairs:
                ind, val = zip(*sorted_pairs)
                results.append({"indices": list(ind), "values": list(val)})
            else:
                results.append({"indices": [], "values": []})
        return results


sparse_service = SparseEmbeddingService()
