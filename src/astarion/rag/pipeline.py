"""Main RAG pipeline orchestrator."""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from .extractor import PDFExtractor, ExtractionConfig
from .chunker import RulebookChunker, ChunkConfig
from .embedder import RulebookEmbedder, EmbeddingConfig
from .retriever import RulebookRetriever, RetrieverConfig


@dataclass
class RAGPipelineConfig:
    """Configuration for the RAG pipeline."""
    extraction_config: Optional[ExtractionConfig] = None
    chunk_config: Optional[ChunkConfig] = None
    embedding_config: Optional[EmbeddingConfig] = None
    retriever_config: Optional[RetrieverConfig] = None
    show_progress: bool = True


class RAGPipeline:
    """Orchestrates the complete RAG pipeline for rulebook processing."""
    
    def __init__(self, config: Optional[RAGPipelineConfig] = None):
        """Initialize the RAG pipeline."""
        self.config = config or RAGPipelineConfig()
        
        # Initialize components
        self.extractor = PDFExtractor(self.config.extraction_config)
        self.chunker = RulebookChunker(self.config.chunk_config)
        self.embedder = RulebookEmbedder(self.config.embedding_config)
        self.retriever = RulebookRetriever(
            self.embedder,
            self.config.retriever_config
        )
        
        logger.info("RAG pipeline initialized")
        
    async def process_pdf(
        self,
        pdf_path: Path,
        game_system: str,
        book_name: Optional[str] = None,
        version: Optional[str] = None,
        recreate_collection: bool = False
    ) -> Dict[str, Any]:
        """Process a PDF through the complete pipeline."""
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Ensure path exists
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
        # Use filename as book name if not provided
        if not book_name:
            book_name = pdf_path.stem
            
        results = {
            "pdf_path": str(pdf_path),
            "game_system": game_system,
            "book_name": book_name,
            "version": version,
            "stages": {}
        }
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            disable=not self.config.show_progress
        ) as progress:
            
            # Stage 1: Extract content
            extract_task = progress.add_task("Extracting content...", total=100)
            extracted_content = await self.extractor.extract_pdf(
                pdf_path,
                book_name,
                version
            )
            progress.update(extract_task, completed=100)
            
            results["stages"]["extraction"] = {
                "content_items": len(extracted_content),
                "content_types": self._count_content_types(extracted_content)
            }
            
            # Stage 2: Chunk content
            chunk_task = progress.add_task("Chunking content...", total=100)
            chunks = await self.chunker.chunk_content(extracted_content)
            progress.update(chunk_task, completed=100)
            
            results["stages"]["chunking"] = {
                "chunks_created": len(chunks),
                "avg_chunk_size": sum(len(c.text) for c in chunks) / len(chunks) if chunks else 0
            }
            
            # Stage 3: Generate embeddings
            embed_task = progress.add_task(
                f"Generating embeddings...", 
                total=len(chunks)
            )
            
            # Process in batches and update progress
            embeddings = []
            batch_size = self.embedder.config.batch_size
            
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_embeddings = await self.embedder.generate_embeddings(
                    batch,
                    show_progress=False
                )
                embeddings.extend(batch_embeddings)
                progress.update(embed_task, advance=len(batch))
                
            results["stages"]["embedding"] = {
                "embeddings_generated": len(embeddings),
                "model": self.embedder.config.model_name,
                "dimension": self.embedder.get_embedding_dimension()
            }
            
            # Stage 4: Index in Qdrant
            index_task = progress.add_task("Indexing in Qdrant...", total=100)
            
            # Create or recreate collection
            await self.retriever.create_collection(
                game_system,
                recreate=recreate_collection
            )
            
            # Index embeddings
            indexed_count = await self.retriever.index_embeddings(
                embeddings,
                game_system
            )
            progress.update(index_task, completed=100)
            
            results["stages"]["indexing"] = {
                "indexed_count": indexed_count,
                "collection": f"{self.retriever.config.collection_prefix}_{game_system.lower()}"
            }
            
        # Get final stats
        results["collection_stats"] = await self.retriever.get_collection_stats(game_system)
        
        logger.info(f"PDF processing complete: {indexed_count} vectors indexed")
        return results
        
    async def search(
        self,
        query: str,
        game_system: str,
        limit: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        content_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Search for content in the indexed rulebooks."""
        # Convert content type strings to enum if provided
        from .extractor import ContentType
        
        if content_types:
            content_type_enums = [
                ContentType(ct) for ct in content_types
            ]
        else:
            content_type_enums = None
            
        # Perform search
        results = await self.retriever.search(
            query=query,
            game_system=game_system,
            limit=limit,
            filters=filters,
            content_types=content_type_enums
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.text,
                "score": result.score,
                "citation": result.get_citation(),
                "source_reference": result.source_reference,
                "metadata": result.metadata
            })
            
        return formatted_results
        
    async def find_similar(
        self,
        reference_text: str,
        game_system: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find content similar to reference text."""
        results = await self.retriever.search_similar(
            reference_text=reference_text,
            game_system=game_system,
            limit=limit
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "text": result.text,
                "score": result.score,
                "citation": result.get_citation(),
                "source_reference": result.source_reference,
                "metadata": result.metadata
            })
            
        return formatted_results
        
    def _count_content_types(self, content: List[Any]) -> Dict[str, int]:
        """Count content by type."""
        counts = {}
        for item in content:
            content_type = item.content_type.value
            counts[content_type] = counts.get(content_type, 0) + 1
        return counts
        
    async def get_stats(self, game_system: str) -> Dict[str, Any]:
        """Get statistics about the indexed content."""
        return await self.retriever.get_collection_stats(game_system) 