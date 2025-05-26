"""Tests for intelligent chunking functionality."""

import pytest

from astarion.rag.chunker import (
    RulebookChunker, RulebookChunk, ChunkConfig
)
from astarion.rag.extractor import ExtractedContent, ContentType


class TestRulebookChunker:
    """Test suite for rulebook chunker."""
    
    def test_init_default_config(self):
        """Test chunker initialization with default config."""
        chunker = RulebookChunker()
        assert chunker.config.chunk_size == 1000
        assert chunker.config.chunk_overlap == 200
        assert chunker.config.preserve_tables is True
        
    def test_init_custom_config(self):
        """Test chunker initialization with custom config."""
        config = ChunkConfig(
            chunk_size=500,
            chunk_overlap=50,
            preserve_spells=False,
            semantic_chunking=False
        )
        chunker = RulebookChunker(config)
        assert chunker.config.chunk_size == 500
        assert chunker.config.preserve_spells is False
        
    @pytest.mark.asyncio
    async def test_chunk_tables(self, sample_extracted_content):
        """Test table chunking."""
        chunker = RulebookChunker()
        
        # Filter for table content
        table_content = [c for c in sample_extracted_content if c.content_type == ContentType.TABLE]
        chunks = await chunker.chunk_content(table_content)
        
        assert len(chunks) > 0
        assert all(chunk.chunk_type == ContentType.TABLE for chunk in chunks)
        
        # Tables should be preserved as single chunks when small
        for chunk in chunks:
            assert "| Level | Proficiency Bonus | Features |" in chunk.text
            
    @pytest.mark.asyncio
    async def test_chunk_large_table(self):
        """Test chunking of large tables."""
        chunker = RulebookChunker(ChunkConfig(chunk_size=100))
        
        # Create a large table
        rows = ["| A | B | C |", "| --- | --- | --- |"]
        for i in range(50):
            rows.append(f"| Row {i} | Data {i} | Value {i} |")
            
        large_table = ExtractedContent(
            content_type=ContentType.TABLE,
            text="\n".join(rows),
            page_number=1
        )
        
        chunks = await chunker.chunk_content([large_table])
        
        # Should be split into multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should have the header
        for chunk in chunks:
            assert "| A | B | C |" in chunk.text
            
    @pytest.mark.asyncio
    async def test_chunk_spells(self, sample_extracted_content):
        """Test spell chunking."""
        chunker = RulebookChunker()
        
        spell_content = [c for c in sample_extracted_content if c.content_type == ContentType.SPELL]
        chunks = await chunker.chunk_content(spell_content)
        
        assert len(chunks) > 0
        for chunk in chunks:
            assert chunk.chunk_type == ContentType.SPELL
            assert "spell_name" in chunk.metadata
            assert "spell_level" in chunk.metadata
            
    def test_extract_spell_metadata(self):
        """Test spell metadata extraction."""
        chunker = RulebookChunker()
        
        # Test spell name extraction
        spell_text = "Fireball\n3rd-level evocation"
        assert chunker._extract_spell_name(spell_text) == "Fireball"
        
        # Test spell level extraction
        assert chunker._extract_spell_level(spell_text) == "3"
        assert chunker._extract_spell_level("Magic Missile\n1st-level evocation") == "1"
        assert chunker._extract_spell_level("Fire Bolt\nCantrip") == "0"
        
        # Test spell school extraction
        assert chunker._extract_spell_school(spell_text) == "Evocation"
        assert chunker._extract_spell_school("Shield\n1st-level abjuration") == "Abjuration"
        
    def test_extract_feat_metadata(self):
        """Test feat metadata extraction."""
        chunker = RulebookChunker()
        
        feat_text = "Great Weapon Master\nPrerequisite: Strength 13 or higher"
        
        assert chunker._extract_feat_name(feat_text) == "Great Weapon Master"
        assert chunker._extract_prerequisites(feat_text) == "Strength 13 or higher"
        
        # Test no prerequisites
        no_prereq = "Lucky\nYou have inexplicable luck"
        assert chunker._extract_prerequisites(no_prereq) == "None"
        
    @pytest.mark.asyncio
    async def test_semantic_chunking(self):
        """Test semantic boundary detection."""
        chunker = RulebookChunker(ChunkConfig(
            chunk_size=200,
            semantic_chunking=True
        ))
        
        # Text with clear semantic boundaries
        text_content = ExtractedContent(
            content_type=ContentType.TEXT,
            text="""
            Fighter
            
            The fighter is a master of martial combat.
            
            Hit Points
            Hit Dice: 1d10 per fighter level
            Hit Points at 1st Level: 10 + Constitution modifier
            
            Proficiencies
            Armor: All armor, shields
            Weapons: Simple weapons, martial weapons
            """.strip(),
            page_number=1
        )
        
        chunks = await chunker.chunk_content([text_content])
        
        # Should split at semantic boundaries
        assert len(chunks) > 1
        
    def test_combine_related_texts(self):
        """Test combining related text items."""
        chunker = RulebookChunker()
        
        texts = [
            ExtractedContent(
                content_type=ContentType.TEXT,
                text="This text ends with a colon:",
                page_number=1
            ),
            ExtractedContent(
                content_type=ContentType.TEXT,
                text="This continues the previous text",
                page_number=1
            ),
            ExtractedContent(
                content_type=ContentType.TEXT,
                text="This is separate",
                page_number=2
            )
        ]
        
        combined = chunker._combine_related_texts(texts)
        
        # First two should be combined
        assert len(combined) == 2
        assert "This text ends with a colon:\nThis continues" in combined[0].text
        
    def test_find_best_split(self):
        """Test finding semantic split points."""
        chunker = RulebookChunker(ChunkConfig(chunk_size=50))
        
        # Text with paragraph boundary
        text = "First paragraph here.\n\nSecond paragraph starts here and continues."
        split = chunker._find_best_split(text)
        assert text[split:].strip().startswith("Second paragraph")
        
        # Text with sentence boundary
        text2 = "First sentence ends here. Second sentence starts and goes on for a while."
        split2 = chunker._find_best_split(text2)
        assert text2[split2:].strip().startswith("Second sentence")
        
    @pytest.mark.asyncio
    async def test_chunk_preservation_settings(self):
        """Test that preservation settings work correctly."""
        # Disable spell preservation
        chunker = RulebookChunker(ChunkConfig(
            preserve_spells=False,
            chunk_size=50
        ))
        
        spell = ExtractedContent(
            content_type=ContentType.SPELL,
            text="Fireball " * 50,  # Long spell text
            page_number=1
        )
        
        chunks = await chunker.chunk_content([spell])
        
        # Without preservation, long spells should be split
        assert len(chunks) > 1 