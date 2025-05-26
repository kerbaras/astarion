"""Intelligent chunking for rulebook content."""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from loguru import logger
from langchain.text_splitter import RecursiveCharacterTextSplitter

from .extractor import ExtractedContent, ContentType


@dataclass
class ChunkConfig:
    """Configuration for chunking."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    min_chunk_size: int = 100
    max_chunk_size: int = 2000
    preserve_tables: bool = True
    preserve_spells: bool = True
    preserve_feats: bool = True
    semantic_chunking: bool = True


class RulebookChunk:
    """A chunk of rulebook content with metadata."""
    
    def __init__(
        self,
        text: str,
        metadata: Dict[str, Any],
        chunk_type: ContentType,
        source_content: Optional[ExtractedContent] = None
    ):
        self.text = text
        self.metadata = metadata
        self.chunk_type = chunk_type
        self.source_content = source_content
        
        # Add standard metadata
        self.metadata.update({
            "chunk_type": chunk_type.value,
            "text_length": len(text),
        })
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "text": self.text,
            "metadata": self.metadata,
            "chunk_type": self.chunk_type.value,
        }


class RulebookChunker:
    """Intelligent chunking for RPG rulebook content."""
    
    def __init__(self, config: Optional[ChunkConfig] = None):
        """Initialize the chunker."""
        self.config = config or ChunkConfig()
        
        # Base text splitter for fallback
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )
        
        # Patterns for semantic boundaries
        self.boundary_patterns = {
            "spell_end": [
                r"\n(?=\w+\n\d+(?:st|nd|rd|th)-level)",
                r"\n(?=\w+\nCantrip)",
            ],
            "feat_end": [
                r"\n(?=\w+\nPrerequisite:)",
                r"\n(?=[A-Z][^.]*\nYou gain)",
            ],
            "section_end": [
                r"\n(?=Chapter \d+)",
                r"\n(?=[A-Z][^.]*\n={3,})",
                r"\n(?=\d+\.\d+ [A-Z])",  # Numbered sections
            ],
            "class_feature_end": [
                r"\n(?=\w+\nStarting at \d+(?:st|nd|rd|th) level)",
                r"\n(?=\w+\nAt \d+(?:st|nd|rd|th) level)",
            ],
        }
        
    async def chunk_content(
        self,
        extracted_content: List[ExtractedContent]
    ) -> List[RulebookChunk]:
        """Chunk extracted content intelligently."""
        logger.info(f"Chunking {len(extracted_content)} content items")
        
        chunks = []
        
        # Group content by type for specialized chunking
        content_by_type = self._group_by_type(extracted_content)
        
        # Process each content type
        for content_type, items in content_by_type.items():
            if content_type == ContentType.TABLE and self.config.preserve_tables:
                chunks.extend(self._chunk_tables(items))
            elif content_type == ContentType.SPELL and self.config.preserve_spells:
                chunks.extend(self._chunk_spells(items))
            elif content_type == ContentType.FEAT and self.config.preserve_feats:
                chunks.extend(self._chunk_feats(items))
            elif content_type in [ContentType.HEADING, ContentType.TEXT]:
                chunks.extend(await self._chunk_text_semantic(items))
            else:
                chunks.extend(self._chunk_generic(items))
                
        logger.info(f"Created {len(chunks)} chunks")
        return chunks
        
    def _group_by_type(
        self,
        content: List[ExtractedContent]
    ) -> Dict[ContentType, List[ExtractedContent]]:
        """Group content by type."""
        grouped = {}
        for item in content:
            if item.content_type not in grouped:
                grouped[item.content_type] = []
            grouped[item.content_type].append(item)
        return grouped
        
    def _chunk_tables(self, tables: List[ExtractedContent]) -> List[RulebookChunk]:
        """Chunk tables - usually keep them whole."""
        chunks = []
        
        for table in tables:
            # Check if table is too large
            if len(table.text) > self.config.max_chunk_size:
                # Split large tables by rows
                rows = table.text.split('\n')
                header = rows[:2]  # Keep header with each chunk
                
                current_chunk = header.copy()
                current_size = sum(len(row) for row in current_chunk)
                
                for row in rows[2:]:
                    if current_size + len(row) > self.config.chunk_size:
                        # Create chunk
                        chunk_text = '\n'.join(current_chunk)
                        chunk = RulebookChunk(
                            text=chunk_text,
                            metadata=table.metadata.copy(),
                            chunk_type=ContentType.TABLE,
                            source_content=table
                        )
                        chunks.append(chunk)
                        
                        # Start new chunk with header
                        current_chunk = header.copy()
                        current_size = sum(len(row) for row in current_chunk)
                        
                    current_chunk.append(row)
                    current_size += len(row)
                    
                # Add final chunk
                if len(current_chunk) > len(header):
                    chunk_text = '\n'.join(current_chunk)
                    chunk = RulebookChunk(
                        text=chunk_text,
                        metadata=table.metadata.copy(),
                        chunk_type=ContentType.TABLE,
                        source_content=table
                    )
                    chunks.append(chunk)
            else:
                # Keep table as single chunk
                chunk = RulebookChunk(
                    text=table.text,
                    metadata=table.metadata.copy(),
                    chunk_type=ContentType.TABLE,
                    source_content=table
                )
                chunks.append(chunk)
                
        return chunks
        
    def _chunk_spells(self, spells: List[ExtractedContent]) -> List[RulebookChunk]:
        """Chunk spells - keep individual spells together."""
        chunks = []
        
        for spell in spells:
            # Each spell is its own chunk
            chunk = RulebookChunk(
                text=spell.text,
                metadata={
                    **spell.metadata,
                    "spell_name": self._extract_spell_name(spell.text),
                    "spell_level": self._extract_spell_level(spell.text),
                    "spell_school": self._extract_spell_school(spell.text),
                },
                chunk_type=ContentType.SPELL,
                source_content=spell
            )
            chunks.append(chunk)
            
        return chunks
        
    def _chunk_feats(self, feats: List[ExtractedContent]) -> List[RulebookChunk]:
        """Chunk feats - keep individual feats together."""
        chunks = []
        
        for feat in feats:
            # Each feat is its own chunk
            chunk = RulebookChunk(
                text=feat.text,
                metadata={
                    **feat.metadata,
                    "feat_name": self._extract_feat_name(feat.text),
                    "prerequisites": self._extract_prerequisites(feat.text),
                },
                chunk_type=ContentType.FEAT,
                source_content=feat
            )
            chunks.append(chunk)
            
        return chunks
        
    async def _chunk_text_semantic(
        self,
        texts: List[ExtractedContent]
    ) -> List[RulebookChunk]:
        """Chunk text content using semantic boundaries."""
        chunks = []
        
        # Combine related text items
        combined_texts = self._combine_related_texts(texts)
        
        for combined in combined_texts:
            if self.config.semantic_chunking:
                # Find semantic boundaries
                text_chunks = self._split_by_semantic_boundaries(combined.text)
            else:
                # Fall back to simple splitting
                text_chunks = self.text_splitter.split_text(combined.text)
                
            for chunk_text in text_chunks:
                if len(chunk_text) < self.config.min_chunk_size:
                    continue
                    
                chunk = RulebookChunk(
                    text=chunk_text,
                    metadata=combined.metadata.copy(),
                    chunk_type=combined.content_type,
                    source_content=combined
                )
                chunks.append(chunk)
                
        return chunks
        
    def _chunk_generic(self, items: List[ExtractedContent]) -> List[RulebookChunk]:
        """Generic chunking for unclassified content."""
        chunks = []
        
        for item in items:
            # Simple text splitting
            if len(item.text) > self.config.chunk_size:
                text_chunks = self.text_splitter.split_text(item.text)
                for chunk_text in text_chunks:
                    chunk = RulebookChunk(
                        text=chunk_text,
                        metadata=item.metadata.copy(),
                        chunk_type=item.content_type,
                        source_content=item
                    )
                    chunks.append(chunk)
            else:
                chunk = RulebookChunk(
                    text=item.text,
                    metadata=item.metadata.copy(),
                    chunk_type=item.content_type,
                    source_content=item
                )
                chunks.append(chunk)
                
        return chunks
        
    def _combine_related_texts(
        self,
        texts: List[ExtractedContent]
    ) -> List[ExtractedContent]:
        """Combine text items that belong together."""
        if not texts:
            return []
            
        combined = []
        current = texts[0]
        
        for next_item in texts[1:]:
            # Check if items should be combined
            if self._should_combine(current, next_item):
                # Combine texts
                current.text += "\n" + next_item.text
                # Merge metadata
                current.metadata.update(next_item.metadata)
            else:
                combined.append(current)
                current = next_item
                
        combined.append(current)
        return combined
        
    def _should_combine(
        self,
        item1: ExtractedContent,
        item2: ExtractedContent
    ) -> bool:
        """Determine if two items should be combined."""
        # Same page and adjacent
        if item1.page_number == item2.page_number:
            # Check if second item continues first
            if item1.text.endswith(":") or item1.text.endswith("-"):
                return True
            # Both are regular text
            if (item1.content_type == ContentType.TEXT and 
                item2.content_type == ContentType.TEXT):
                return True
                
        return False
        
    def _split_by_semantic_boundaries(self, text: str) -> List[str]:
        """Split text at semantic boundaries."""
        chunks = []
        remaining = text
        
        while remaining:
            # Find the best split point
            split_point = self._find_best_split(remaining)
            
            if split_point == -1 or split_point >= len(remaining) - 1:
                chunks.append(remaining)
                break
                
            chunk = remaining[:split_point].strip()
            if chunk:
                chunks.append(chunk)
            remaining = remaining[split_point:].strip()
            
        return chunks
        
    def _find_best_split(self, text: str) -> int:
        """Find the best semantic split point."""
        if len(text) <= self.config.chunk_size:
            return -1
            
        # Look for semantic boundaries
        for pattern_list in self.boundary_patterns.values():
            for pattern in pattern_list:
                match = re.search(pattern, text[:self.config.chunk_size * 2])
                if match:
                    return match.start()
                    
        # Fall back to paragraph boundary
        para_end = text.find("\n\n", self.config.chunk_size)
        if para_end != -1:
            return para_end
            
        # Fall back to sentence boundary
        sentence_end = re.search(r'\. (?=[A-Z])', text[self.config.chunk_size:])
        if sentence_end:
            return self.config.chunk_size + sentence_end.end()
            
        # Last resort - split at chunk size
        return self.config.chunk_size
        
    def _extract_spell_name(self, text: str) -> str:
        """Extract spell name from spell text."""
        lines = text.split('\n')
        if lines:
            return lines[0].strip()
        return "Unknown Spell"
        
    def _extract_spell_level(self, text: str) -> str:
        """Extract spell level from spell text."""
        match = re.search(r'(\d+)(?:st|nd|rd|th)-level', text)
        if match:
            return match.group(1)
        if 'cantrip' in text.lower():
            return "0"
        return "Unknown"
        
    def _extract_spell_school(self, text: str) -> str:
        """Extract spell school from spell text."""
        schools = [
            "abjuration", "conjuration", "divination", "enchantment",
            "evocation", "illusion", "necromancy", "transmutation"
        ]
        text_lower = text.lower()
        for school in schools:
            if school in text_lower:
                return school.capitalize()
        return "Unknown"
        
    def _extract_feat_name(self, text: str) -> str:
        """Extract feat name from feat text."""
        lines = text.split('\n')
        if lines:
            return lines[0].strip()
        return "Unknown Feat"
        
    def _extract_prerequisites(self, text: str) -> str:
        """Extract prerequisites from feat text."""
        match = re.search(r'Prerequisite[s]?:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return "None" 