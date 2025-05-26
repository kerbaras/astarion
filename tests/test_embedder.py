"""Tests for embedding generation functionality."""

import pytest
import numpy as np

from astarion.rag.embedder import (
    RulebookEmbedder, EmbeddingConfig, EmbeddingResult
)
from astarion.rag.chunker import RulebookChunk
from astarion.rag.extractor import ContentType


class TestRulebookEmbedder:
    """Test suite for embeddings."""
    
    @pytest.mark.asyncio
    async def test_init_default_config(self):
        """Test embedder initialization with default config."""
        embedder = RulebookEmbedder()
        assert embedder.config.model_name == "all-MiniLM-L6-v2"
        assert embedder.config.normalize_embeddings is True
        assert embedder.get_embedding_dimension() == 384
        
    @pytest.mark.asyncio
    async def test_init_custom_config(self):
        """Test embedder initialization with custom config."""
        config = EmbeddingConfig(
            model_name="all-MiniLM-L6-v2",
            batch_size=16,
            normalize_embeddings=False,
            cache_embeddings=False
        )
        embedder = RulebookEmbedder(config)
        assert embedder.config.batch_size == 16
        assert embedder.config.normalize_embeddings is False
        
    @pytest.mark.asyncio
    async def test_generate_embeddings_single_chunk(self, sample_chunks):
        """Test generating embeddings for a single chunk."""
        embedder = RulebookEmbedder(EmbeddingConfig(cache_embeddings=False))
        
        results = await embedder.generate_embeddings([sample_chunks[0]])
        
        assert len(results) == 1
        assert isinstance(results[0], EmbeddingResult)
        assert results[0].embedding.shape == (384,)
        assert results[0].chunk == sample_chunks[0]
        
    @pytest.mark.asyncio
    async def test_generate_embeddings_batch(self, sample_chunks):
        """Test generating embeddings for multiple chunks."""
        embedder = RulebookEmbedder(EmbeddingConfig(
            batch_size=2,
            cache_embeddings=False
        ))
        
        results = await embedder.generate_embeddings(sample_chunks)
        
        assert len(results) == len(sample_chunks)
        for i, result in enumerate(results):
            assert result.chunk == sample_chunks[i]
            assert result.embedding.shape == (384,)
            
    @pytest.mark.asyncio
    async def test_embedding_caching(self, sample_chunks):
        """Test that embedding caching works."""
        embedder = RulebookEmbedder(EmbeddingConfig(cache_embeddings=True))
        
        # Generate embeddings first time
        results1 = await embedder.generate_embeddings([sample_chunks[0]])
        
        # Generate again - should use cache
        results2 = await embedder.generate_embeddings([sample_chunks[0]])
        
        # Should be the same embedding
        np.testing.assert_array_equal(
            results1[0].embedding,
            results2[0].embedding
        )
        
    @pytest.mark.asyncio
    async def test_prepare_text_for_embedding(self):
        """Test text preparation with metadata."""
        embedder = RulebookEmbedder()
        
        # Spell chunk
        spell_chunk = RulebookChunk(
            text="Fireball spell text",
            metadata={"spell_name": "Fireball"},
            chunk_type=ContentType.SPELL
        )
        
        prepared = embedder._prepare_text_for_embedding(spell_chunk)
        assert "[SPELL]" in prepared
        assert "Spell: Fireball" in prepared
        assert "Fireball spell text" in prepared
        
        # Table chunk
        table_chunk = RulebookChunk(
            text="Table content",
            metadata={"table_type": "weapons"},
            chunk_type=ContentType.TABLE
        )
        
        prepared = embedder._prepare_text_for_embedding(table_chunk)
        assert "[TABLE]" in prepared
        assert "Table: weapons" in prepared
        
    @pytest.mark.asyncio
    async def test_query_embedding_generation(self):
        """Test query embedding generation."""
        embedder = RulebookEmbedder()
        
        # Simple query
        embedding = await embedder.generate_query_embedding("fireball spell")
        assert embedding.shape == (384,)
        
        # Query with context
        embedding_with_context = await embedder.generate_query_embedding(
            "fireball spell",
            context={"content_type": "spell", "game_system": "dnd5e"}
        )
        assert embedding_with_context.shape == (384,)
        
        # Embeddings should be different with context
        assert not np.array_equal(embedding, embedding_with_context)
        
    def test_generate_chunk_id(self):
        """Test chunk ID generation."""
        embedder = RulebookEmbedder()
        
        chunk1 = RulebookChunk(
            text="Test text",
            metadata={},
            chunk_type=ContentType.TEXT
        )
        
        chunk2 = RulebookChunk(
            text="Test text",  # Same text
            metadata={},
            chunk_type=ContentType.SPELL  # Different type
        )
        
        id1 = embedder._generate_chunk_id(chunk1)
        id2 = embedder._generate_chunk_id(chunk2)
        
        # Different chunks should have different IDs
        assert id1 != id2
        assert len(id1) == 16  # SHA256 truncated to 16 chars
        
    @pytest.mark.asyncio
    async def test_token_count_estimation(self):
        """Test token counting."""
        embedder = RulebookEmbedder()
        
        short_text = "Hello world"
        long_text = "This is a much longer text " * 100
        
        short_count = embedder.estimate_token_count(short_text)
        long_count = embedder.estimate_token_count(long_text)
        
        assert short_count < long_count
        assert short_count > 0
        
    @pytest.mark.asyncio
    async def test_text_truncation(self):
        """Test that long texts are truncated."""
        embedder = RulebookEmbedder(EmbeddingConfig(
            max_sequence_length=50
        ))
        
        # Create a very long text
        long_text = "word " * 1000
        chunk = RulebookChunk(
            text=long_text,
            metadata={},
            chunk_type=ContentType.TEXT
        )
        
        prepared = embedder._prepare_text_for_embedding(chunk)
        
        # Should be truncated
        tokens = embedder.estimate_token_count(prepared)
        assert tokens <= 50
        
    def test_get_model_info(self):
        """Test model info retrieval."""
        embedder = RulebookEmbedder()
        
        info = embedder.get_model_info()
        assert info["model_name"] == "all-MiniLM-L6-v2"
        assert info["dimension"] == 384
        assert info["max_sequence_length"] == 512
        assert "device" in info
        
    @pytest.mark.asyncio
    async def test_embedding_normalization(self):
        """Test that embeddings are normalized when configured."""
        embedder = RulebookEmbedder(EmbeddingConfig(
            normalize_embeddings=True
        ))
        
        chunk = RulebookChunk(
            text="Test text",
            metadata={},
            chunk_type=ContentType.TEXT
        )
        
        results = await embedder.generate_embeddings([chunk])
        embedding = results[0].embedding
        
        # Normalized embeddings should have L2 norm of 1
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, rtol=1e-5) 