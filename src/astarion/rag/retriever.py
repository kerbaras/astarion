"""Qdrant-based retrieval for rulebook content."""

import uuid
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, 
    Filter, FieldCondition, Range, MatchValue
)
from loguru import logger

from .embedder import RulebookEmbedder, EmbeddingResult
from .extractor import ContentType


@dataclass
class RetrieverConfig:
    """Configuration for retriever."""
    qdrant_url: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    collection_prefix: str = "astarion_rules"
    search_limit: int = 10
    score_threshold: float = 0.5
    use_reranking: bool = True
    

class SearchResult:
    """A search result from the retriever."""
    
    def __init__(
        self,
        text: str,
        score: float,
        metadata: Dict[str, Any],
        source_reference: Optional[str] = None
    ):
        self.text = text
        self.score = score
        self.metadata = metadata
        self.source_reference = source_reference
        
    def get_citation(self) -> str:
        """Get formatted citation for this result."""
        parts = []
        
        if self.metadata.get("source_book"):
            parts.append(self.metadata["source_book"])
            
        if self.metadata.get("page_number"):
            parts.append(f"p. {self.metadata['page_number']}")
            
        if self.metadata.get("source_version"):
            parts.append(f"v{self.metadata['source_version']}")
            
        return ", ".join(parts) if parts else "Unknown Source"


class RulebookRetriever:
    """Retrieve relevant content from rulebooks using Qdrant."""
    
    def __init__(
        self,
        embedder: RulebookEmbedder,
        config: Optional[RetrieverConfig] = None
    ):
        """Initialize the retriever."""
        self.embedder = embedder
        self.config = config or RetrieverConfig()
        
        # Initialize Qdrant client
        self.client = QdrantClient(
            url=self.config.qdrant_url,
            port=self.config.qdrant_port,
            api_key=self.config.qdrant_api_key
        )
        
        self.embedding_dimension = embedder.get_embedding_dimension()
        
    async def create_collection(
        self,
        game_system: str,
        recreate: bool = False
    ) -> str:
        """Create or verify collection for a game system."""
        collection_name = f"{self.config.collection_prefix}_{game_system.lower()}"
        
        # Check if collection exists
        collections = self.client.get_collections()
        exists = any(c.name == collection_name for c in collections.collections)
        
        if exists and recreate:
            logger.info(f"Recreating collection: {collection_name}")
            self.client.delete_collection(collection_name)
            exists = False
            
        if not exists:
            logger.info(f"Creating collection: {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dimension,
                    distance=Distance.COSINE
                )
            )
            
        return collection_name
        
    async def index_embeddings(
        self,
        embeddings: List[EmbeddingResult],
        game_system: str,
        batch_size: int = 100
    ) -> int:
        """Index embeddings in Qdrant."""
        collection_name = await self.create_collection(game_system)
        
        logger.info(f"Indexing {len(embeddings)} embeddings in {collection_name}")
        
        # Process in batches
        indexed_count = 0
        
        for i in range(0, len(embeddings), batch_size):
            batch = embeddings[i:i + batch_size]
            points = []
            
            for embedding_result in batch:
                # Create point
                point = PointStruct(
                    id=str(uuid.uuid4()),
                    vector=embedding_result.embedding.tolist(),
                    payload={
                        "text": embedding_result.chunk.text,
                        "chunk_type": embedding_result.chunk.chunk_type.value,
                        "metadata": embedding_result.chunk.metadata,
                        "source_book": embedding_result.chunk.source_content.source_book 
                            if embedding_result.chunk.source_content else None,
                        "source_version": embedding_result.chunk.source_content.source_version
                            if embedding_result.chunk.source_content else None,
                        "page_number": embedding_result.chunk.source_content.page_number
                            if embedding_result.chunk.source_content else None,
                    }
                )
                points.append(point)
                
            # Upload batch
            self.client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            indexed_count += len(points)
            
            if i % (batch_size * 5) == 0:
                logger.info(f"Indexed {indexed_count}/{len(embeddings)} embeddings")
                
        logger.info(f"Indexing complete. Total indexed: {indexed_count}")
        return indexed_count
        
    async def search(
        self,
        query: str,
        game_system: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        content_types: Optional[List[ContentType]] = None
    ) -> List[SearchResult]:
        """Search for relevant content."""
        collection_name = f"{self.config.collection_prefix}_{game_system.lower()}"
        
        # Check if collection exists
        collections = self.client.get_collections()
        if not any(c.name == collection_name for c in collections.collections):
            logger.warning(f"Collection {collection_name} does not exist")
            return []
            
        # Generate query embedding
        query_embedding = await self.embedder.generate_query_embedding(
            query,
            context={"game_system": game_system}
        )
        
        # Build filter
        search_filter = self._build_filter(filters, content_types)
        
        # Search
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit or self.config.search_limit,
            query_filter=search_filter,
            score_threshold=self.config.score_threshold,
            with_payload=True
        )
        
        # Convert to SearchResult objects
        search_results = []
        for result in results:
            search_result = SearchResult(
                text=result.payload.get("text", ""),
                score=result.score,
                metadata=result.payload.get("metadata", {}),
                source_reference=self._format_source_reference(result.payload)
            )
            search_results.append(search_result)
            
        # Rerank if enabled
        if self.config.use_reranking and len(search_results) > 1:
            search_results = await self._rerank_results(query, search_results)
            
        return search_results
        
    async def search_similar(
        self,
        reference_text: str,
        game_system: str,
        limit: Optional[int] = None,
        exclude_self: bool = True
    ) -> List[SearchResult]:
        """Search for content similar to reference text."""
        collection_name = f"{self.config.collection_prefix}_{game_system.lower()}"
        
        # Generate embedding for reference text
        reference_embedding = await self.embedder.generate_query_embedding(reference_text)
        
        # Search with increased limit to allow filtering
        search_limit = (limit or self.config.search_limit) + (1 if exclude_self else 0)
        
        results = self.client.search(
            collection_name=collection_name,
            query_vector=reference_embedding.tolist(),
            limit=search_limit,
            score_threshold=self.config.score_threshold,
            with_payload=True
        )
        
        # Convert and filter
        search_results = []
        for result in results:
            # Skip if it's the same text
            if exclude_self and result.payload.get("text") == reference_text:
                continue
                
            search_result = SearchResult(
                text=result.payload.get("text", ""),
                score=result.score,
                metadata=result.payload.get("metadata", {}),
                source_reference=self._format_source_reference(result.payload)
            )
            search_results.append(search_result)
            
            if len(search_results) >= (limit or self.config.search_limit):
                break
                
        return search_results
        
    def _build_filter(
        self,
        filters: Optional[Dict[str, Any]],
        content_types: Optional[List[ContentType]]
    ) -> Optional[Filter]:
        """Build Qdrant filter from parameters."""
        conditions = []
        
        # Content type filter
        if content_types:
            type_values = [ct.value for ct in content_types]
            conditions.append(
                FieldCondition(
                    key="chunk_type",
                    match=MatchValue(any=type_values)
                )
            )
            
        # Custom filters
        if filters:
            for key, value in filters.items():
                if isinstance(value, (list, tuple)):
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(any=value)
                        )
                    )
                elif isinstance(value, dict) and "min" in value:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(
                                gte=value.get("min"),
                                lte=value.get("max")
                            )
                        )
                    )
                else:
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value)
                        )
                    )
                    
        if conditions:
            return Filter(must=conditions)
        return None
        
    def _format_source_reference(self, payload: Dict[str, Any]) -> str:
        """Format source reference from payload."""
        parts = []
        
        if payload.get("source_book"):
            parts.append(payload["source_book"])
            
        if payload.get("page_number"):
            parts.append(f"p. {payload['page_number']}")
            
        metadata = payload.get("metadata", {})
        if metadata.get("table_type"):
            parts.append(f"({metadata['table_type']} table)")
        elif payload.get("chunk_type"):
            parts.append(f"({payload['chunk_type']})")
            
        return " - ".join(parts) if parts else "Unknown Source"
        
    async def _rerank_results(
        self,
        query: str,
        results: List[SearchResult]
    ) -> List[SearchResult]:
        """Rerank results for better relevance."""
        # Simple reranking based on exact matches and metadata
        for result in results:
            boost = 1.0
            
            # Boost exact matches
            if query.lower() in result.text.lower():
                boost *= 1.5
                
            # Boost based on content type relevance
            if "spell" in query.lower() and result.metadata.get("chunk_type") == "spell":
                boost *= 1.3
            elif "feat" in query.lower() and result.metadata.get("chunk_type") == "feat":
                boost *= 1.3
            elif "table" in query.lower() and result.metadata.get("chunk_type") == "table":
                boost *= 1.2
                
            # Apply boost
            result.score *= boost
            
        # Re-sort by boosted scores
        results.sort(key=lambda r: r.score, reverse=True)
        
        return results
        
    async def get_collection_stats(self, game_system: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        collection_name = f"{self.config.collection_prefix}_{game_system.lower()}"
        
        try:
            info = self.client.get_collection(collection_name)
            return {
                "collection_name": collection_name,
                "vector_count": info.vectors_count,
                "indexed_count": info.indexed_vectors_count,
                "status": info.status,
                "config": {
                    "dimension": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance
                }
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "collection_name": collection_name,
                "error": str(e)
            } 