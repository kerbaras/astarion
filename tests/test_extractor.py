"""Tests for PDF extraction functionality."""

import pytest
from pathlib import Path

from astarion.rag.extractor import (
    PDFExtractor, ExtractedContent, ContentType, ExtractionConfig
)


class TestPDFExtractor:
    """Test suite for PDF extractor."""
    
    def test_init_default_config(self):
        """Test extractor initialization with default config."""
        extractor = PDFExtractor()
        assert extractor.config.extract_tables is True
        assert extractor.config.clean_headers_footers is True
        assert extractor.config.min_text_length == 10
        
    def test_init_custom_config(self):
        """Test extractor initialization with custom config."""
        config = ExtractionConfig(
            extract_tables=False,
            min_text_length=20,
            detect_columns=False
        )
        extractor = PDFExtractor(config)
        assert extractor.config.extract_tables is False
        assert extractor.config.min_text_length == 20
        
    def test_content_classification(self):
        """Test content type classification."""
        extractor = PDFExtractor()
        
        # Test spell classification
        spell_content = ExtractedContent(
            content_type=ContentType.TEXT,
            text="Fireball\n3rd-level evocation\nCasting Time: 1 action",
            page_number=1
        )
        classified = extractor._classify_content([spell_content])
        assert classified[0].content_type == ContentType.SPELL
        
        # Test feat classification
        feat_content = ExtractedContent(
            content_type=ContentType.TEXT,
            text="Alert\nPrerequisite: None\nYou gain a +5 bonus",
            page_number=1
        )
        classified = extractor._classify_content([feat_content])
        assert classified[0].content_type == ContentType.FEAT
        
        # Test class feature classification
        feature_content = ExtractedContent(
            content_type=ContentType.TEXT,
            text="Starting at 3rd level, you can use your action",
            page_number=1
        )
        classified = extractor._classify_content([feature_content])
        assert classified[0].content_type == ContentType.CLASS_FEATURE
        
    def test_table_to_markdown(self):
        """Test table to markdown conversion."""
        extractor = PDFExtractor()
        
        table = [
            ["Level", "Bonus", "Features"],
            ["1st", "+2", "Rage"],
            ["2nd", "+2", "Reckless Attack"]
        ]
        
        markdown = extractor._table_to_markdown(table)
        assert "| Level | Bonus | Features |" in markdown
        assert "| --- | --- | --- |" in markdown
        assert "| 1st | +2 | Rage |" in markdown
        
    def test_table_type_identification(self):
        """Test table type identification."""
        extractor = PDFExtractor()
        
        # Spell table
        spell_headers = ["Spell Name", "Level", "Casting Time"]
        assert extractor._identify_table_type(spell_headers) == "spell_list"
        
        # Weapon table
        weapon_headers = ["Weapon", "Damage", "Properties"]
        assert extractor._identify_table_type(weapon_headers) == "weapons"
        
        # Armor table
        armor_headers = ["Armor", "AC", "Stealth"]
        assert extractor._identify_table_type(armor_headers) == "armor"
        
    def test_clean_content(self):
        """Test content cleaning."""
        extractor = PDFExtractor()
        
        content = [
            ExtractedContent(
                content_type=ContentType.TEXT,
                text="  This   has   extra   spaces  ",
                page_number=1
            ),
            ExtractedContent(
                content_type=ContentType.TEXT,
                text="42",  # Just a page number
                page_number=42
            ),
            ExtractedContent(
                content_type=ContentType.TEXT,
                text="Too short",  # Below min length
                page_number=1
            )
        ]
        
        cleaned = extractor._clean_content(content)
        assert len(cleaned) == 1
        assert cleaned[0].text == "This has extra spaces"
        
    def test_merge_hyphenated_words(self):
        """Test hyphenated word merging."""
        extractor = PDFExtractor()
        
        text = "This is a hyphen-\nated word and another split-\nword"
        result = extractor._merge_hyphenated_words(text)
        assert result == "This is a hyphenated word and another splitword"
        
    def test_clean_header_footer(self):
        """Test header/footer cleaning."""
        extractor = PDFExtractor()
        
        text = "Chapter 5: Combat\nSome content here\n42"
        result = extractor._clean_header_footer(text, 42)
        assert "42" not in result
        assert "Chapter 5" not in result
        assert "Some content here" in result
        
    @pytest.mark.asyncio
    async def test_extract_pdf_file_not_found(self):
        """Test PDF extraction with non-existent file."""
        extractor = PDFExtractor()
        
        with pytest.raises(Exception):
            await extractor.extract_pdf(Path("/nonexistent/file.pdf"))
            
    def test_is_likely_bold(self):
        """Test bold text detection heuristic."""
        extractor = PDFExtractor()
        
        # All caps text
        assert extractor._is_likely_bold((0, 0, 100, 20, "ALL CAPS TEXT", 0, 0))
        
        # Title case ending with colon
        assert extractor._is_likely_bold((0, 0, 100, 20, "Title:", 0, 0))
        
        # Regular text
        assert not extractor._is_likely_bold((0, 0, 100, 20, "Regular text here", 0, 0)) 