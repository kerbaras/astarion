# Astarion RAG System Documentation

## Overview

The Astarion RAG (Retrieval-Augmented Generation) system is designed to process, index, and query tabletop RPG rulebooks. It provides intelligent extraction, chunking, and semantic search capabilities specifically tailored for RPG content.

## Architecture

### Components

1. **PDF Extractor** (`extractor.py`)
   - Uses PyMuPDF for text extraction
   - Uses pdfplumber for table extraction
   - Classifies content into types (spells, feats, rules, etc.)
   - Preserves page numbers and metadata

2. **Intelligent Chunker** (`chunker.py`)
   - Semantic chunking based on content type
   - Preserves complete spells, feats, and tables
   - Smart boundary detection for rules
   - Configurable chunk sizes and overlap

3. **Embedder** (`embedder.py`)
   - Uses sentence-transformers for embedding generation
   - Contextual embedding with metadata
   - Batch processing for efficiency
   - Caching support for repeated content

4. **Qdrant Retriever** (`retriever.py`)
   - Vector similarity search
   - Metadata filtering
   - Source citation tracking
   - Reranking for improved relevance

5. **RAG Pipeline** (`pipeline.py`)
   - Orchestrates the complete workflow
   - Progress tracking
   - Error handling and recovery

## Usage

### Starting Qdrant

```bash
# Start Qdrant vector database
docker-compose up -d qdrant

# Verify it's running
curl http://localhost:6333/dashboard
```

### Processing a Rulebook

```python
from astarion.rag.pipeline import RAGPipeline

# Initialize pipeline
pipeline = RAGPipeline()

# Process a PDF
result = await pipeline.process_pdf(
    pdf_path="path/to/phb.pdf",
    game_system="dnd5e",
    book_name="PHB",
    version="5.14"
)
```

### Searching for Rules

```python
from astarion.agents.ruleset import RulesetAgent

# Initialize agent
agent = RulesetAgent()

# Query for a spell
spell = await agent.find_spell("fireball", GameSystem.DND5E)
print(f"Found: {spell.text}")
print(f"Source: {spell.citation}")

# Check prerequisites
prereq = await agent.check_prerequisite("Great Weapon Master")
print(f"Prerequisites: {prereq}")

# Look up a table
table = await agent.lookup_table("wild magic surge")
print(f"Table: {table.text}")
```

### Advanced Queries

```python
# Search with filters
results = await pipeline.search(
    query="two-weapon fighting rules",
    game_system="dnd5e",
    content_types=["rule", "feat"],
    limit=5
)

# Find similar content
similar = await pipeline.find_similar(
    reference_text="When you take the Attack action...",
    game_system="dnd5e"
)
```

## Content Types

The system recognizes and specially handles:

- **Spells**: Complete spell blocks with all components
- **Feats**: Full feat descriptions with prerequisites
- **Tables**: Preserved table structure in markdown
- **Class Features**: Level-based abilities
- **Equipment**: Items with stats and properties
- **Rules**: General game mechanics
- **Monsters**: Stat blocks (future)

## Configuration

### Extraction Settings
```python
ExtractionConfig(
    extract_tables=True,      # Extract tables
    extract_images=False,     # Skip images (for now)
    clean_headers_footers=True,
    merge_hyphenated=True,
    min_text_length=10
)
```

### Chunking Settings
```python
ChunkConfig(
    chunk_size=1000,         # Target chunk size
    chunk_overlap=200,       # Overlap between chunks
    preserve_tables=True,    # Keep tables intact
    preserve_spells=True,    # Keep spells intact
    preserve_feats=True,     # Keep feats intact
    semantic_chunking=True   # Use semantic boundaries
)
```

### Embedding Settings
```python
EmbeddingConfig(
    model_name="all-MiniLM-L6-v2",  # Fast and good
    max_sequence_length=512,
    batch_size=32,
    normalize_embeddings=True,
    cache_embeddings=True
)
```

## Best Practices

1. **PDF Quality**: Higher quality PDFs extract better
2. **Book Naming**: Use consistent abbreviations (PHB, DMG, XGE)
3. **Versioning**: Track rulebook versions for errata
4. **Batch Processing**: Process multiple books together
5. **Regular Reindexing**: Reindex when extraction improves

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**
   ```bash
   # Check if Qdrant is running
   docker ps | grep qdrant
   
   # Check logs
   docker logs astarion_qdrant_1
   ```

2. **PDF Extraction Issues**
   - Try different PDF readers
   - Check if PDF is text-based (not scanned)
   - Some PDFs may need OCR

3. **Memory Issues**
   - Reduce batch_size in embedding config
   - Process books one at a time
   - Increase Docker memory limits

## Performance

- **Extraction**: ~1-2 seconds per page
- **Chunking**: <1 second per 100 chunks  
- **Embedding**: ~10-20 chunks per second
- **Indexing**: ~100 vectors per second
- **Search**: <100ms per query

## Future Enhancements

1. **OCR Support**: For scanned rulebooks
2. **Image Extraction**: Diagrams and illustrations
3. **Multi-modal Search**: Text + image queries
4. **Incremental Updates**: Add pages without full reindex
5. **Cross-reference Resolution**: Link related rules
6. **LLM Enhancement**: Use LLM for better classification 