"""Embedding generation for rulebook content."""

import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
import tiktoken

from .chunker import RulebookChunk


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""
    model_name: str = "all-MiniLM-L6-v2"  # Good balance of speed and quality
    max_sequence_length: int = 512
    batch_size: int = 32
    normalize_embeddings: bool = True
    cache_embeddings: bool = True
    device: Optional[str] = None  # None for auto-detect


class EmbeddingResult:
    """Result of embedding generation."""
    
    def __init__(
        self,
        chunk: RulebookChunk,
        embedding: np.ndarray,
        embedding_id: str,
        model_name: str
    ):
        self.chunk = chunk
        self.embedding = embedding
        self.embedding_id = embedding_id
        self.model_name = model_name
        self.dimension = len(embedding)
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.embedding_id,
            "embedding": self.embedding.tolist(),
            "dimension": self.dimension,
            "model": self.model_name,
            "text": self.chunk.text,
            "metadata": self.chunk.metadata,
        }


class RulebookEmbedder:
    """Generate embeddings for rulebook content."""
    
    def __init__(self, config: Optional[EmbeddingConfig] = None):
        """Initialize the embedder."""
        self.config = config or EmbeddingConfig()
        
        # Initialize the model
        logger.info(f"Loading embedding model: {self.config.model_name}")
        self.model = SentenceTransformer(
            self.config.model_name,
            device=self.config.device
        )
        
        # Set max sequence length
        self.model.max_seq_length = self.config.max_sequence_length
        
        # Initialize tokenizer for token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            
        # Cache for embeddings if enabled
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
        logger.info(f"Embedder initialized with dimension: {self.model.get_sentence_embedding_dimension()}")
        
    async def generate_embeddings(
        self,
        chunks: List[RulebookChunk],
        show_progress: bool = True
    ) -> List[EmbeddingResult]:
        """Generate embeddings for chunks."""
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        results = []
        
        # Process in batches
        for i in range(0, len(chunks), self.config.batch_size):
            batch = chunks[i:i + self.config.batch_size]
            batch_results = await self._process_batch(batch)
            results.extend(batch_results)
            
            if show_progress and i % (self.config.batch_size * 5) == 0:
                logger.info(f"Processed {i + len(batch)}/{len(chunks)} chunks")
                
        logger.info(f"Generated {len(results)} embeddings")
        return results
        
    async def _process_batch(
        self,
        chunks: List[RulebookChunk]
    ) -> List[EmbeddingResult]:
        """Process a batch of chunks."""
        results = []
        
        # Prepare texts with metadata context
        texts_to_embed = []
        chunks_to_process = []
        
        for chunk in chunks:
            # Check cache
            chunk_id = self._generate_chunk_id(chunk)
            
            if self.config.cache_embeddings and chunk_id in self._embedding_cache:
                # Use cached embedding
                embedding = self._embedding_cache[chunk_id]
                result = EmbeddingResult(
                    chunk=chunk,
                    embedding=embedding,
                    embedding_id=chunk_id,
                    model_name=self.config.model_name
                )
                results.append(result)
            else:
                # Prepare for embedding
                text = self._prepare_text_for_embedding(chunk)
                texts_to_embed.append(text)
                chunks_to_process.append(chunk)
                
        # Generate embeddings for non-cached chunks
        if texts_to_embed:
            embeddings = self.model.encode(
                texts_to_embed,
                batch_size=self.config.batch_size,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=False
            )
            
            # Create results
            for chunk, embedding in zip(chunks_to_process, embeddings):
                chunk_id = self._generate_chunk_id(chunk)
                
                # Cache if enabled
                if self.config.cache_embeddings:
                    self._embedding_cache[chunk_id] = embedding
                    
                result = EmbeddingResult(
                    chunk=chunk,
                    embedding=embedding,
                    embedding_id=chunk_id,
                    model_name=self.config.model_name
                )
                results.append(result)
                
        return results
        
    def _prepare_text_for_embedding(self, chunk: RulebookChunk) -> str:
        """Prepare text for embedding with context."""
        # Build text with metadata context
        parts = []
        
        # Add type context
        if chunk.chunk_type:
            parts.append(f"[{chunk.chunk_type.value.upper()}]")
            
        # Add specific metadata
        metadata = chunk.metadata
        
        if metadata.get("spell_name"):
            parts.append(f"Spell: {metadata['spell_name']}")
        elif metadata.get("feat_name"):
            parts.append(f"Feat: {metadata['feat_name']}")
        elif metadata.get("table_type"):
            parts.append(f"Table: {metadata['table_type']}")
            
        # Add source context
        if chunk.source_content:
            if chunk.source_content.source_book:
                parts.append(f"Source: {chunk.source_content.source_book}")
                
        # Add main text
        parts.append(chunk.text)
        
        # Combine and truncate if needed
        full_text = " ".join(parts)
        
        # Check token count and truncate if necessary
        tokens = self.tokenizer.encode(full_text)
        if len(tokens) > self.config.max_sequence_length:
            # Truncate to fit
            truncated_tokens = tokens[:self.config.max_sequence_length - 10]  # Leave some margin
            full_text = self.tokenizer.decode(truncated_tokens)
            
        return full_text
        
    def _generate_chunk_id(self, chunk: RulebookChunk) -> str:
        """Generate unique ID for chunk."""
        # Create stable hash from content and key metadata
        content = f"{chunk.chunk_type.value}:{chunk.text}"
        
        # Add key metadata to ensure uniqueness
        if chunk.source_content:
            content += f":{chunk.source_content.page_number}"
            if chunk.source_content.source_book:
                content += f":{chunk.source_content.source_book}"
                
        return hashlib.sha256(content.encode()).hexdigest()[:16]
        
    async def generate_query_embedding(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> np.ndarray:
        """Generate embedding for a search query."""
        # Add context to query if provided
        if context:
            query_parts = []
            
            if context.get("content_type"):
                query_parts.append(f"[{context['content_type'].upper()}]")
                
            if context.get("game_system"):
                query_parts.append(f"System: {context['game_system']}")
                
            query_parts.append(query)
            full_query = " ".join(query_parts)
        else:
            full_query = query
            
        # Generate embedding
        embedding = self.model.encode(
            full_query,
            normalize_embeddings=self.config.normalize_embeddings
        )
        
        return embedding
        
    def estimate_token_count(self, text: str) -> int:
        """Estimate token count for text."""
        return len(self.tokenizer.encode(text))
        
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings."""
        return self.model.get_sentence_embedding_dimension()
        
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model."""
        return {
            "model_name": self.config.model_name,
            "dimension": self.get_embedding_dimension(),
            "max_sequence_length": self.config.max_sequence_length,
            "device": str(self.model.device),
        } 