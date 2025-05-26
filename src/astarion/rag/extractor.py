"""PDF extraction module for rulebook processing."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import pymupdf
import pdfplumber
from loguru import logger
from pydantic import BaseModel


class ContentType(str, Enum):
    """Types of content extracted from PDFs."""
    TEXT = "text"
    TABLE = "table"
    HEADING = "heading"
    SPELL = "spell"
    FEAT = "feat"
    RULE = "rule"
    CLASS_FEATURE = "class_feature"
    EQUIPMENT = "equipment"
    MONSTER = "monster"


class ExtractedContent(BaseModel):
    """Extracted content from PDF."""
    content_type: ContentType
    text: str
    page_number: int
    metadata: Dict[str, Any] = {}
    bbox: Optional[Tuple[float, float, float, float]] = None
    source_book: Optional[str] = None
    source_version: Optional[str] = None


@dataclass
class ExtractionConfig:
    """Configuration for PDF extraction."""
    extract_tables: bool = True
    extract_images: bool = False
    clean_headers_footers: bool = True
    merge_hyphenated: bool = True
    min_text_length: int = 10
    detect_columns: bool = True


class PDFExtractor:
    """Extract structured content from RPG rulebook PDFs."""
    
    def __init__(self, config: Optional[ExtractionConfig] = None):
        """Initialize the PDF extractor."""
        self.config = config or ExtractionConfig()
        
        # Patterns for detecting different content types
        self.patterns = {
            ContentType.SPELL: [
                r"^(.+?)\n\d+(?:st|nd|rd|th)-level",
                r"^(.+?)\nCantrip",
                r"Casting Time:",
                r"Range:",
                r"Components:",
            ],
            ContentType.FEAT: [
                r"Prerequisite:",
                r"You gain the following benefits:",
                r"^(.+?)\n.*?feat",
            ],
            ContentType.CLASS_FEATURE: [
                r"Starting at \d+(?:st|nd|rd|th) level",
                r"At \d+(?:st|nd|rd|th) level",
                r"Beginning at \d+(?:st|nd|rd|th) level",
            ],
            ContentType.EQUIPMENT: [
                r"(?:Cost|Price):\s*\d+\s*(?:cp|sp|gp|pp)",
                r"(?:Weight|Wt)\.?:\s*\d+\s*(?:lb\.|lbs?)",
                r"(?:AC|Armor Class):\s*\d+",
                r"Damage:\s*\d+d\d+",
            ],
        }
        
    async def extract_pdf(
        self, 
        pdf_path: Path,
        book_name: Optional[str] = None,
        version: Optional[str] = None
    ) -> List[ExtractedContent]:
        """Extract all content from a PDF file."""
        logger.info(f"Extracting content from {pdf_path}")
        
        content = []
        
        # Extract text and structure with PyMuPDF
        pymupdf_content = await self._extract_with_pymupdf(pdf_path, book_name, version)
        content.extend(pymupdf_content)
        
        # Extract tables with pdfplumber
        if self.config.extract_tables:
            table_content = await self._extract_tables_with_pdfplumber(pdf_path, book_name, version)
            content.extend(table_content)
            
        # Post-process and classify content
        content = self._classify_content(content)
        
        # Clean and merge content
        content = self._clean_content(content)
        
        logger.info(f"Extracted {len(content)} content items from {pdf_path}")
        return content
        
    async def _extract_with_pymupdf(
        self,
        pdf_path: Path,
        book_name: Optional[str],
        version: Optional[str]
    ) -> List[ExtractedContent]:
        """Extract text content using PyMuPDF."""
        content = []
        
        try:
            doc = pymupdf.open(str(pdf_path))
            
            for page_num, page in enumerate(doc, 1):
                # Get text blocks
                blocks = page.get_text("blocks")
                
                for block in blocks:
                    # Skip if block is an image
                    if block[6] == 1:  # Block type 1 is image
                        continue
                        
                    text = block[4].strip()
                    
                    # Skip empty or too short text
                    if not text or len(text) < self.config.min_text_length:
                        continue
                        
                    # Clean text
                    if self.config.clean_headers_footers:
                        text = self._clean_header_footer(text, page_num)
                        
                    if self.config.merge_hyphenated:
                        text = self._merge_hyphenated_words(text)
                        
                    # Create extracted content
                    extracted = ExtractedContent(
                        content_type=ContentType.TEXT,
                        text=text,
                        page_number=page_num,
                        bbox=(block[0], block[1], block[2], block[3]),
                        source_book=book_name,
                        source_version=version,
                        metadata={
                            "font_size": self._estimate_font_size(block),
                            "is_bold": self._is_likely_bold(block),
                        }
                    )
                    
                    content.append(extracted)
                    
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting with PyMuPDF: {e}")
            raise
            
        return content
        
    async def _extract_tables_with_pdfplumber(
        self,
        pdf_path: Path,
        book_name: Optional[str],
        version: Optional[str]
    ) -> List[ExtractedContent]:
        """Extract tables using pdfplumber."""
        content = []
        
        try:
            with pdfplumber.open(str(pdf_path)) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()
                    
                    for table_idx, table in enumerate(tables):
                        if not table or not table[0]:  # Skip empty tables
                            continue
                            
                        # Convert table to markdown format
                        table_text = self._table_to_markdown(table)
                        
                        # Identify table type based on headers
                        table_type = self._identify_table_type(table[0])
                        
                        extracted = ExtractedContent(
                            content_type=ContentType.TABLE,
                            text=table_text,
                            page_number=page_num,
                            source_book=book_name,
                            source_version=version,
                            metadata={
                                "table_index": table_idx,
                                "rows": len(table),
                                "columns": len(table[0]) if table else 0,
                                "table_type": table_type,
                            }
                        )
                        
                        content.append(extracted)
                        
        except Exception as e:
            logger.error(f"Error extracting tables with pdfplumber: {e}")
            # Don't raise - tables are optional
            
        return content
        
    def _classify_content(self, content: List[ExtractedContent]) -> List[ExtractedContent]:
        """Classify content based on patterns and context."""
        for item in content:
            if item.content_type != ContentType.TEXT:
                continue
                
            # Check against patterns
            for content_type, patterns in self.patterns.items():
                for pattern in patterns:
                    if re.search(pattern, item.text, re.IGNORECASE | re.MULTILINE):
                        item.content_type = content_type
                        break
                        
            # Additional classification based on metadata
            if item.metadata.get("is_bold") and len(item.text) < 100:
                item.content_type = ContentType.HEADING
                
        return content
        
    def _clean_content(self, content: List[ExtractedContent]) -> List[ExtractedContent]:
        """Clean and normalize extracted content."""
        cleaned = []
        
        for item in content:
            # Remove extra whitespace
            item.text = re.sub(r'\s+', ' ', item.text).strip()
            
            # Remove page numbers that appear as standalone items
            if re.match(r'^\d+$', item.text):
                continue
                
            # Skip very short items unless they're headings
            if len(item.text) < self.config.min_text_length and item.content_type != ContentType.HEADING:
                continue
                
            cleaned.append(item)
            
        return cleaned
        
    def _clean_header_footer(self, text: str, page_num: int) -> str:
        """Remove common header/footer patterns."""
        # Remove page numbers
        text = re.sub(rf'\b{page_num}\b', '', text)
        
        # Remove common footer patterns
        text = re.sub(r'Chapter \d+.*?$', '', text, flags=re.IGNORECASE)
        
        return text.strip()
        
    def _merge_hyphenated_words(self, text: str) -> str:
        """Merge words split by hyphens at line breaks."""
        return re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
        
    def _estimate_font_size(self, block: tuple) -> float:
        """Estimate font size from block height."""
        height = block[3] - block[1]
        # Rough estimation - needs refinement
        return height / len(block[4].split('\n')) if block[4] else 12
        
    def _is_likely_bold(self, block: tuple) -> bool:
        """Heuristic to detect if text is likely bold."""
        # This is a simplified check - would need font info for accuracy
        text = block[4]
        return (
            text.isupper() or
            re.match(r'^[A-Z][A-Z\s]+$', text) or
            len(text) < 50 and text.endswith(':')
        )
        
    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """Convert table to markdown format."""
        if not table:
            return ""
            
        lines = []
        
        # Header
        header = table[0]
        lines.append("| " + " | ".join(str(cell or "") for cell in header) + " |")
        lines.append("| " + " | ".join("---" for _ in header) + " |")
        
        # Rows
        for row in table[1:]:
            lines.append("| " + " | ".join(str(cell or "") for cell in row) + " |")
            
        return "\n".join(lines)
        
    def _identify_table_type(self, headers: List[str]) -> str:
        """Identify table type based on headers."""
        headers_text = " ".join(str(h).lower() for h in headers if h)
        
        if any(word in headers_text for word in ["spell", "level", "casting"]):
            return "spell_list"
        elif any(word in headers_text for word in ["weapon", "damage", "properties"]):
            return "weapons"
        elif any(word in headers_text for word in ["armor", "ac", "stealth"]):
            return "armor"
        elif any(word in headers_text for word in ["skill", "ability", "modifier"]):
            return "skills"
        elif any(word in headers_text for word in ["feat", "prerequisite", "benefit"]):
            return "feats"
        else:
            return "generic" 