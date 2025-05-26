"""PDF processor for rulebook ingestion."""

from pathlib import Path
from typing import Optional, List, Dict, Any

from loguru import logger

from astarion.core.config import get_settings
from .pipeline import RAGPipeline, RAGPipelineConfig
from .extractor import ExtractionConfig
from .chunker import ChunkConfig
from .embedder import EmbeddingConfig
from .retriever import RetrieverConfig


class RulebookProcessor:
    """Process rulebook PDFs and index them for RAG."""
    
    def __init__(self):
        """Initialize the processor."""
        self.settings = get_settings()
        
        # Configure RAG pipeline
        pipeline_config = RAGPipelineConfig(
            extraction_config=ExtractionConfig(
                extract_tables=True,
                clean_headers_footers=True,
                merge_hyphenated=True
            ),
            chunk_config=ChunkConfig(
                chunk_size=1000,
                chunk_overlap=200,
                preserve_tables=True,
                preserve_spells=True,
                preserve_feats=True,
                semantic_chunking=True
            ),
            embedding_config=EmbeddingConfig(
                model_name=self.settings.embedding_model,
                max_sequence_length=512,
                batch_size=32,
                normalize_embeddings=True
            ),
            retriever_config=RetrieverConfig(
                qdrant_url=self.settings.qdrant_url.split(":")[0] if ":" in self.settings.qdrant_url else self.settings.qdrant_url,
                qdrant_port=int(self.settings.qdrant_url.split(":")[1]) if ":" in self.settings.qdrant_url else 6333,
                qdrant_api_key=self.settings.qdrant_api_key,
                collection_prefix="astarion_rules",
                search_limit=10,
                use_reranking=True
            ),
            show_progress=True
        )
        
        # Initialize pipeline
        self.pipeline = RAGPipeline(pipeline_config)
        
    async def process_pdf(
        self, 
        pdf_path: str,
        system: str = "dnd5e",
        book_name: Optional[str] = None,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Process a PDF rulebook and index it.
        
        Args:
            pdf_path: Path to the PDF file
            system: Game system (e.g., 'dnd5e')
            book_name: Book name/abbreviation (e.g., 'PHB')
            version: Book version
            
        Returns:
            Processing results including number of pages and chunks
        """
        # Use the RAG pipeline
        result = await self.pipeline.process_pdf(
            pdf_path=Path(pdf_path),
            game_system=system,
            book_name=book_name,
            version=version,
            recreate_collection=False
        )
        
        return result
        
    async def search(
        self,
        query: str,
        system: Optional[str] = None,
        limit: int = 5,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks."""
        # Use the RAG pipeline search
        results = await self.pipeline.search(
            query=query,
            game_system=system or "dnd5e",
            limit=limit,
            content_types=content_types
        )
        
        return results
        
    async def get_stats(self, system: str = "dnd5e") -> Dict[str, Any]:
        """Get statistics about indexed content."""
        return await self.pipeline.get_stats(system) 