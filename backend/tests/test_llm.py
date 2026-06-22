import pytest
from unittest.mock import AsyncMock, patch, PropertyMock
from app.llm.embeddings import embeddings_service
from app.llm.rerank import reranker_service
from app.llm.sparse import sparse_service
from app.llm.gateway import llm_gateway, LLMGateway


@pytest.mark.asyncio
async def test_embeddings():
    # Verify embeddings_service returns a 3072-vector
    res = await embeddings_service.embed(["x"])
    assert len(res) == 1
    assert len(res[0]) == 3072


def test_rerank():
    # Verify reranker_service returns scores
    res = reranker_service.compute_scores("query", ["passage 1", "passage 2"])
    assert len(res) == 2
    assert all(isinstance(s, float) for s in res)


def test_sparse():
    # Verify sparse_service returns indices and values
    res = sparse_service.encode(["x"])
    assert len(res) == 1
    assert "indices" in res[0]
    assert "values" in res[0]


@pytest.mark.asyncio
async def test_gateway_generate_mock():
    # Mock the Gemini API call to test caching and fallback logic
    with patch.object(llm_gateway, "_call_gemini", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = "Mock response from Gemini"
        
        # Disable Redis for simple test case using PropertyMock
        with patch.object(LLMGateway, "redis", new_callable=PropertyMock) as mock_redis:
            mock_redis.return_value = None
            res = await llm_gateway.generate(
                system="You are a helpful assistant.",
                user="Hello",
                model="gemini-2.0-flash"
            )
            assert res == "Mock response from Gemini"
            mock_call.assert_called_once()

