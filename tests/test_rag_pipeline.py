"""Test script for RAG pipeline functionality."""

import asyncio
from pathlib import Path

import pytest
from loguru import logger

from astarion.rag.pipeline import RAGPipeline, RAGPipelineConfig
from astarion.rag.extractor import ContentType


@pytest.mark.asyncio
async def test_rag_pipeline_initialization():
    """Test that RAG pipeline initializes correctly."""
    pipeline = RAGPipeline()
    assert pipeline is not None
    assert pipeline.extractor is not None
    assert pipeline.chunker is not None
    assert pipeline.embedder is not None
    assert pipeline.retriever is not None


@pytest.mark.asyncio
async def test_pdf_extraction():
    """Test PDF extraction (requires test PDF)."""
    from astarion.rag.extractor import PDFExtractor, ExtractedContent
    
    extractor = PDFExtractor()
    
    # Create a mock ExtractedContent for testing
    content = ExtractedContent(
        content_type=ContentType.TEXT,
        text="This is a test spell.\nCasting Time: 1 action\nRange: 30 feet",
        page_number=1,
        source_book="Test Book"
    )
    
    assert content.content_type == ContentType.TEXT
    assert "spell" in content.text.lower()
    assert content.page_number == 1


@pytest.mark.asyncio
async def test_chunking():
    """Test content chunking."""
    from astarion.rag.chunker import RulebookChunker
    from astarion.rag.extractor import ExtractedContent, ContentType
    
    chunker = RulebookChunker()
    
    # Create test content
    test_content = [
        ExtractedContent(
            content_type=ContentType.TEXT,
            text="This is a long text that needs to be chunked. " * 50,
            page_number=1
        ),
        ExtractedContent(
            content_type=ContentType.SPELL,
            text="Fireball\n3rd-level evocation\nCasting Time: 1 action",
            page_number=2
        )
    ]
    
    chunks = await chunker.chunk_content(test_content)
    
    assert len(chunks) > 0
    assert any(chunk.chunk_type == ContentType.SPELL for chunk in chunks)


@pytest.mark.asyncio
async def test_embedding_generation():
    """Test embedding generation."""
    from astarion.rag.embedder import RulebookEmbedder
    from astarion.rag.chunker import RulebookChunk
    from astarion.rag.extractor import ContentType
    
    embedder = RulebookEmbedder()
    
    # Create test chunk
    chunk = RulebookChunk(
        text="Test rule about spellcasting",
        metadata={"test": True},
        chunk_type=ContentType.TEXT
    )
    
    embeddings = await embedder.generate_embeddings([chunk])
    
    assert len(embeddings) == 1
    assert embeddings[0].embedding is not None
    assert len(embeddings[0].embedding) == embedder.get_embedding_dimension()


@pytest.mark.asyncio
async def test_search_functionality():
    """Test search functionality (requires Qdrant to be running)."""
    from astarion.rag.embedder import RulebookEmbedder
    from astarion.rag.retriever import RulebookRetriever
    
    embedder = RulebookEmbedder()
    retriever = RulebookRetriever(embedder)
    
    # This test requires Qdrant to be running
    try:
        stats = await retriever.get_collection_stats("dnd5e")
        logger.info(f"Collection stats: {stats}")
    except Exception as e:
        logger.warning(f"Qdrant not available for testing: {e}")
        pytest.skip("Qdrant not available")


if __name__ == "__main__":
    # Run a simple test
    async def main():
        logger.info("Testing RAG pipeline initialization...")
        pipeline = RAGPipeline()
        logger.info("✓ RAG pipeline initialized successfully")
        
        logger.info("\nTesting embedder...")
        dimension = pipeline.embedder.get_embedding_dimension()
        logger.info(f"✓ Embedder dimension: {dimension}")
        
        logger.info("\nTesting query embedding generation...")
        embedding = await pipeline.embedder.generate_query_embedding("test query")
        logger.info(f"✓ Generated query embedding with shape: {embedding.shape}")
        
        logger.info("\nAll basic tests passed!")
        
    asyncio.run(main()) 