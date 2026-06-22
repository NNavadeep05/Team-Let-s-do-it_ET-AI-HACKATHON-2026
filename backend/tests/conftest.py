import sys
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy import event
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, CITEXT

# Mock heavy/external packages before they are imported by app modules
class MockTextEmbedding:
    def embed(self, texts):
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


# =====================================================================
# SQLAlchemy SQLite Dialect Compilers for PostgreSQL specific types
# =====================================================================

@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(element, compiler, **kw):
    return "JSON"


@compiles(ARRAY, "sqlite")
def compile_array_sqlite(element, compiler, **kw):
    return "TEXT"


@compiles(CITEXT, "sqlite")
def compile_citext_sqlite(element, compiler, **kw):
    return "TEXT"


# =====================================================================
# Intercept metadata creation to remove Postgres-specific indices on SQLite
# =====================================================================

from app.db.base import Base

@event.listens_for(Base.metadata, "before_create")
def remove_pg_only_indexes(target, connection, **kw):
    if connection.dialect.name == "sqlite":
        for table in target.tables.values():
            indices_to_remove = set()
            for idx in table.indexes:
                # Check expressions or index kwargs
                expr_str = ""
                try:
                    expr_str = str(idx.expressions)
                except Exception:
                    expr_str = str(idx.columns)
                    
                if "to_tsvector" in expr_str or idx.kwargs.get("postgresql_using") == "gin":
                    indices_to_remove.add(idx)
            table.indexes.difference_update(indices_to_remove)
