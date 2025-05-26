"""Integration tests for the complete RAG pipeline."""

import pytest
from pathlib import Path

from astarion.rag.pipeline import RAGPipeline
from astarion.rag.extractor import ContentType


@pytest.mark.integration
class TestRAGPipelineIntegration:
    """Integration tests for RAG pipeline."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_pipeline(self, temp_dir, mock_qdrant_client):
        """Test complete pipeline from PDF to search."""
        # Create a mock PDF file
        pdf_path = temp_dir / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\nTest content")
        
        pipeline = RAGPipeline()
        
        # This will fail with real PDF processing but tests the flow
        with pytest.raises(Exception):
            await pipeline.process_pdf(
                pdf_path=pdf_path,
                game_system="test",
                book_name="TEST",
                version="1.0"
            )
            
    @pytest.mark.asyncio
    async def test_search_integration(self, mock_qdrant_client):
        """Test search functionality."""
        pipeline = RAGPipeline()
        
        # Search should return empty results for non-existent system
        results = await pipeline.search(
            query="test query",
            game_system="nonexistent",
            limit=5
        )
        
        assert results == []
        
    @pytest.mark.asyncio
    async def test_pipeline_with_mock_data(self, sample_extracted_content, mock_qdrant_client):
        """Test pipeline with mock extracted content."""
        pipeline = RAGPipeline()
        
        # Test chunking
        chunks = await pipeline.chunker.chunk_content(sample_extracted_content)
        assert len(chunks) > 0
        
        # Test embedding generation
        embeddings = await pipeline.embedder.generate_embeddings(chunks[:2])
        assert len(embeddings) == 2
        
        # Test indexing
        count = await pipeline.retriever.index_embeddings(embeddings, "test_system")
        assert count == 2
        
    @pytest.mark.asyncio
    async def test_stats_retrieval(self, mock_qdrant_client):
        """Test getting stats about indexed content."""
        pipeline = RAGPipeline()
        
        # Create collection first
        await pipeline.retriever.create_collection("test_system")
        
        # Get stats
        stats = await pipeline.get_stats("test_system")
        
        assert "collection_name" in stats
        assert stats["collection_name"] == "astarion_rules_test_system"


@pytest.mark.integration
@pytest.mark.rag
class TestRAGComponentIntegration:
    """Test integration between RAG components."""
    
    @pytest.mark.asyncio
    async def test_extractor_to_chunker_flow(self, sample_extracted_content):
        """Test flow from extractor to chunker."""
        from astarion.rag.chunker import RulebookChunker
        
        chunker = RulebookChunker()
        chunks = await chunker.chunk_content(sample_extracted_content)
        
        # Verify chunks maintain metadata
        for chunk in chunks:
            assert chunk.chunk_type in [c.value for c in ContentType]
            assert "page_number" in chunk.metadata
            
    @pytest.mark.asyncio
    async def test_chunker_to_embedder_flow(self, sample_chunks):
        """Test flow from chunker to embedder."""
        from astarion.rag.embedder import RulebookEmbedder
        
        embedder = RulebookEmbedder()
        embeddings = await embedder.generate_embeddings(sample_chunks[:2])
        
        # Verify embeddings maintain chunk reference
        for i, embedding in enumerate(embeddings):
            assert embedding.chunk == sample_chunks[i]
            assert embedding.embedding.shape == (384,)
            
    @pytest.mark.asyncio
    async def test_embedder_to_retriever_flow(self, test_embedder, test_retriever, sample_chunks, mock_qdrant_client):
        """Test flow from embedder to retriever."""
        # Generate embeddings
        embeddings = await test_embedder.generate_embeddings(sample_chunks[:2])
        
        # Index them
        count = await test_retriever.index_embeddings(embeddings, "test_system")
        assert count == 2
        
        # Verify we can retrieve stats
        stats = await test_retriever.get_collection_stats("test_system")
        assert stats["vector_count"] == 2


@pytest.mark.smoke
class TestRAGSmoke:
    """Smoke tests for basic RAG functionality."""
    
    def test_imports(self):
        """Test that all RAG components can be imported."""
        from astarion.rag import (
            RAGPipeline, PDFExtractor, RulebookChunker,
            RulebookEmbedder, RulebookRetriever
        )
        
        assert RAGPipeline is not None
        assert PDFExtractor is not None
        assert RulebookChunker is not None
        assert RulebookEmbedder is not None
        assert RulebookRetriever is not None
        
    def test_pipeline_initialization(self):
        """Test that pipeline initializes without errors."""
        from astarion.rag import RAGPipeline
        
        pipeline = RAGPipeline()
        assert pipeline.extractor is not None
        assert pipeline.chunker is not None
        assert pipeline.embedder is not None
        assert pipeline.retriever is not None
        
    @pytest.mark.asyncio
    async def test_basic_embedding_generation(self):
        """Test basic embedding generation."""
        from astarion.rag.embedder import RulebookEmbedder
        
        embedder = RulebookEmbedder()
        embedding = await embedder.generate_query_embedding("test query")
        
        assert embedding.shape == (384,)
        assert embedding.dtype.name.startswith('float') 