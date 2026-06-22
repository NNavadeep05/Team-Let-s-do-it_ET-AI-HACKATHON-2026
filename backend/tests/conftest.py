import sys
from unittest.mock import MagicMock, AsyncMock

# Mock heavy/external packages before they are imported by app modules
class MockTextEmbedding:
    def embed(self, texts):
        # Mock embeddings (e.g. BAAI/bge-small-en-v1.5 has 384 dimensions)
        return [[0.1] * 384 for _ in texts]

class MockSparseEmbedding:
    def embed(self, texts):
        class MockSparse:
            def __init__(self):
                self.indices = [1, 2, 3]
                self.values = [0.5, 0.6, 0.7]
        return [MockSparse() for _ in texts]

class MockReranker:
    def __init__(self, *args, **kwargs):
        pass
    def compute_score(self, pairs):
        return [0.9] * len(pairs)

# Configure mock modules
sys.modules['openai'] = MagicMock()

mock_fastembed = MagicMock()
mock_fastembed.TextEmbedding = MockTextEmbedding
mock_fastembed.SparseTextEmbedding = MockSparseEmbedding
sys.modules['fastembed'] = mock_fastembed

mock_flag = MagicMock()
mock_flag.FlagReranker = MockReranker
sys.modules['FlagEmbedding'] = mock_flag

# Mock google.generativeai
mock_genai = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = mock_genai
sys.modules['google.generativeai.types'] = MagicMock()

# Mock redis
sys.modules['redis'] = MagicMock()
