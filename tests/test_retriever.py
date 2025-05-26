"""Tests for Qdrant-based retrieval functionality."""

import pytest
import numpy as np
from unittest.mock import MagicMock

from astarion.rag.retriever import (
    RulebookRetriever, RetrieverConfig, SearchResult
)
from astarion.rag.embedder import EmbeddingResult
from astarion.rag.extractor import ContentType


class TestRulebookRetriever:
    """Test suite for retriever."""
    
    @pytest.mark.asyncio
    async def test_init_default_config(self, test_embedder, mock_qdrant_client):
        """Test retriever initialization with default config."""
        retriever = RulebookRetriever(test_embedder)
        assert retriever.config.collection_prefix == "astarion_rules"
        assert retriever.config.search_limit == 10
        assert retriever.config.use_reranking is True
        
    @pytest.mark.asyncio
    async def test_create_collection(self, test_retriever, mock_qdrant_client):
        """Test collection creation."""
        collection_name = await test_retriever.create_collection("test_system")
        assert collection_name == "test_astarion_test_system"
        
        # Verify collection was created
        collections = test_retriever.client.get_collections()
        assert any(c.name == collection_name for c in collections.collections)
        
    @pytest.mark.asyncio
    async def test_create_collection_recreate(self, test_retriever, mock_qdrant_client):
        """Test collection recreation."""
        # Create collection
        collection_name = await test_retriever.create_collection("test_system")
        
        # Recreate it
        collection_name2 = await test_retriever.create_collection("test_system", recreate=True)
        assert collection_name == collection_name2
        
    @pytest.mark.asyncio
    async def test_index_embeddings(self, test_retriever, sample_chunks, mock_qdrant_client):
        """Test indexing embeddings."""
        # Create mock embeddings
        embeddings = []
        for chunk in sample_chunks[:2]:
            embedding_result = EmbeddingResult(
                chunk=chunk,
                embedding=np.random.randn(384),
                embedding_id=f"test_{chunk.text[:10]}",
                model_name="test"
            )
            embeddings.append(embedding_result)
            
        # Index them
        count = await test_retriever.index_embeddings(embeddings, "test_system")
        assert count == 2
        
    @pytest.mark.asyncio
    async def test_search_no_collection(self, test_retriever, mock_qdrant_client):
        """Test search when collection doesn't exist."""
        results = await test_retriever.search(
            query="test query",
            game_system="nonexistent_system"
        )
        assert results == []
        
    @pytest.mark.asyncio
    async def test_search_basic(self, test_retriever, mock_qdrant_client):
        """Test basic search functionality."""
        # Create collection first
        await test_retriever.create_collection("test_system")
        
        # Mock search results
        from types import SimpleNamespace
        mock_results = [
            SimpleNamespace(
                score=0.9,
                payload={
                    "text": "Fireball spell text",
                    "chunk_type": "spell",
                    "metadata": {"spell_name": "Fireball"},
                    "source_book": "PHB",
                    "page_number": 241
                }
            ),
            SimpleNamespace(
                score=0.8,
                payload={
                    "text": "Fire Bolt cantrip",
                    "chunk_type": "spell",
                    "metadata": {"spell_name": "Fire Bolt"},
                    "source_book": "PHB",
                    "page_number": 242
                }
            )
        ]
        
        # Patch the search method
        test_retriever.client.search = MagicMock(return_value=mock_results)
        
        # Perform search
        results = await test_retriever.search(
            query="fire spells",
            game_system="test_system",
            limit=5
        )
        
        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)
        assert results[0].score > results[1].score
        assert "Fireball" in results[0].text
        
    @pytest.mark.asyncio
    async def test_search_with_filters(self, test_retriever, mock_qdrant_client):
        """Test search with metadata filters."""
        await test_retriever.create_collection("test_system")
        
        # Test with content type filter
        results = await test_retriever.search(
            query="test",
            game_system="test_system",
            content_types=[ContentType.SPELL, ContentType.FEAT]
        )
        
        # Verify filter was built correctly
        test_retriever.client.search.assert_called()
        call_args = test_retriever.client.search.call_args
        assert call_args.kwargs.get("query_filter") is not None
        
    def test_build_filter(self, test_retriever):
        """Test filter building."""
        # Test with content types
        filter1 = test_retriever._build_filter(None, [ContentType.SPELL])
        assert filter1 is not None
        
        # Test with custom filters
        filter2 = test_retriever._build_filter(
            {"source_book": "PHB", "level": {"min": 1, "max": 3}},
            None
        )
        assert filter2 is not None
        
        # Test with no filters
        filter3 = test_retriever._build_filter(None, None)
        assert filter3 is None
        
    def test_format_source_reference(self, test_retriever):
        """Test source reference formatting."""
        # Test with full info
        ref1 = test_retriever._format_source_reference({
            "source_book": "PHB",
            "page_number": 241,
            "chunk_type": "spell"
        })
        assert ref1 == "PHB - p. 241 - (spell)"
        
        # Test with partial info
        ref2 = test_retriever._format_source_reference({
            "source_book": "DMG"
        })
        assert ref2 == "DMG"
        
        # Test with table
        ref3 = test_retriever._format_source_reference({
            "metadata": {"table_type": "weapons"}
        })
        assert "(weapons table)" in ref3
        
    @pytest.mark.asyncio
    async def test_rerank_results(self, test_retriever):
        """Test result reranking."""
        # Create mock results
        results = [
            SearchResult(
                text="Some other spell",
                score=0.9,
                metadata={"chunk_type": "spell"}
            ),
            SearchResult(
                text="fireball is a great spell",
                score=0.8,
                metadata={"chunk_type": "spell"}
            ),
            SearchResult(
                text="Great Weapon Master feat",
                score=0.85,
                metadata={"chunk_type": "feat"}
            )
        ]
        
        # Rerank with spell query
        reranked = await test_retriever._rerank_results("fireball spell", results)
        
        # Fireball result should be boosted
        assert "fireball" in reranked[0].text.lower()
        assert reranked[0].score > 0.9  # Boosted from 0.8
        
    @pytest.mark.asyncio
    async def test_search_similar(self, test_retriever, mock_qdrant_client):
        """Test similar content search."""
        await test_retriever.create_collection("test_system")
        
        # Mock results
        from types import SimpleNamespace
        mock_results = [
            SimpleNamespace(
                score=1.0,
                payload={"text": "Reference text"}  # Exact match
            ),
            SimpleNamespace(
                score=0.9,
                payload={"text": "Similar text"}
            )
        ]
        
        test_retriever.client.search = MagicMock(return_value=mock_results)
        
        # Search for similar
        results = await test_retriever.search_similar(
            reference_text="Reference text",
            game_system="test_system",
            exclude_self=True
        )
        
        # Should exclude the exact match
        assert len(results) == 1
        assert results[0].text == "Similar text"
        
    @pytest.mark.asyncio
    async def test_get_collection_stats(self, test_retriever, mock_qdrant_client):
        """Test getting collection statistics."""
        await test_retriever.create_collection("test_system")
        
        stats = await test_retriever.get_collection_stats("test_system")
        
        assert "collection_name" in stats
        assert "vector_count" in stats
        assert stats["config"]["dimension"] == 384
        
    @pytest.mark.asyncio
    async def test_get_collection_stats_error(self, test_retriever, mock_qdrant_client):
        """Test getting stats for non-existent collection."""
        stats = await test_retriever.get_collection_stats("nonexistent")
        
        assert "error" in stats
        assert stats["collection_name"] == "test_astarion_nonexistent"
        
    def test_search_result_citation(self):
        """Test SearchResult citation formatting."""
        result = SearchResult(
            text="Test",
            score=0.9,
            metadata={
                "source_book": "PHB",
                "page_number": 42,
                "source_version": "5.14"
            }
        )
        
        citation = result.get_citation()
        assert citation == "PHB, p. 42, v5.14"
        
        # Test with missing info
        result2 = SearchResult(
            text="Test",
            score=0.9,
            metadata={}
        )
        assert result2.get_citation() == "Unknown Source" 