"""Pytest configuration and shared fixtures."""

import asyncio
import tempfile
from pathlib import Path
from typing import Generator, AsyncGenerator
import shutil

import pytest
import pytest_asyncio
from loguru import logger

from astarion.rag.extractor import ExtractedContent, ContentType
from astarion.rag.chunker import RulebookChunk
from astarion.rag.embedder import RulebookEmbedder, EmbeddingConfig
from astarion.rag.retriever import RulebookRetriever, RetrieverConfig
from astarion.models.character import Character, GameSystem, AbilityScores, Race, CharacterClass, Background, Equipment


# Configure pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_pdf_content() -> str:
    """Sample PDF-like content for testing."""
    return """
    Fireball
    3rd-level evocation
    Casting Time: 1 action
    Range: 150 feet
    Components: V, S, M (a tiny ball of bat guano and sulfur)
    Duration: Instantaneous
    
    A bright streak flashes from your pointing finger to a point you choose 
    within range and then blossoms with a low roar into an explosion of flame.
    
    Great Weapon Master
    Prerequisite: None
    You've learned to put the weight of a weapon to your advantage.
    You gain the following benefits:
    • On your turn, when you score a critical hit with a melee weapon
    • Before you make a melee attack with a heavy weapon
    """


@pytest.fixture
def sample_extracted_content() -> list[ExtractedContent]:
    """Sample extracted content for testing."""
    return [
        ExtractedContent(
            content_type=ContentType.SPELL,
            text="Fireball\n3rd-level evocation\nCasting Time: 1 action\nRange: 150 feet",
            page_number=42,
            source_book="PHB",
            source_version="5.14"
        ),
        ExtractedContent(
            content_type=ContentType.FEAT,
            text="Great Weapon Master\nPrerequisite: None\nYou've learned to put the weight of a weapon to your advantage.",
            page_number=167,
            source_book="PHB",
            source_version="5.14"
        ),
        ExtractedContent(
            content_type=ContentType.TABLE,
            text="| Level | Proficiency Bonus | Features |\n| --- | --- | --- |\n| 1st | +2 | Rage |",
            page_number=46,
            source_book="PHB",
            source_version="5.14",
            metadata={"table_type": "class_progression"}
        ),
        ExtractedContent(
            content_type=ContentType.TEXT,
            text="The Fighter is a master of martial combat, skilled with a variety of weapons and armor.",
            page_number=70,
            source_book="PHB"
        ),
    ]


@pytest.fixture
def sample_chunks(sample_extracted_content) -> list[RulebookChunk]:
    """Sample chunks for testing."""
    chunks = []
    for content in sample_extracted_content:
        chunk = RulebookChunk(
            text=content.text,
            metadata={
                "page_number": content.page_number,
                "source_book": content.source_book,
            },
            chunk_type=content.content_type,
            source_content=content
        )
        chunks.append(chunk)
    return chunks


@pytest_asyncio.fixture
async def test_embedder() -> RulebookEmbedder:
    """Create a test embedder with fast settings."""
    config = EmbeddingConfig(
        model_name="all-MiniLM-L6-v2",
        batch_size=8,
        cache_embeddings=False  # Disable caching for tests
    )
    return RulebookEmbedder(config)


@pytest_asyncio.fixture
async def test_retriever(test_embedder) -> RulebookRetriever:
    """Create a test retriever."""
    config = RetrieverConfig(
        qdrant_url="localhost",
        qdrant_port=6333,
        collection_prefix="test_astarion",
        search_limit=5
    )
    return RulebookRetriever(test_embedder, config)


@pytest.fixture
def sample_character() -> Character:
    """Create a sample character for testing."""
    return Character(
        name="Test Hero",
        system=GameSystem.DND5E,
        level=1,
        race=Race(
            name="Human",
            traits=["Versatile"],
            ability_bonuses={"strength": 1, "dexterity": 1},
            size="Medium",
            speed=30,
            languages=["Common"]
        ),
        classes=[
            CharacterClass(
                name="Fighter",
                level=1,
                hit_dice="d10",
                primary_ability="strength",
                saving_throws=["strength", "constitution"]
            )
        ],
        background=Background(
            name="Folk Hero",
            skills=["Animal Handling", "Survival"],
            equipment=["Artisan's tools", "Shovel"],
            feature="Rustic Hospitality"
        ),
        ability_scores=AbilityScores(
            strength=16,
            dexterity=14,
            constitution=15,
            intelligence=10,
            wisdom=12,
            charisma=8
        ),
        hit_points=12,
        max_hit_points=12,
        armor_class=16,
        proficiency_bonus=2,
        equipment=Equipment(
            weapons=["Longsword", "Shield"],
            armor="Chain mail",
            shield=True
        )
    )


@pytest.fixture
def mock_pdf_path(temp_dir) -> Path:
    """Create a mock PDF file for testing."""
    pdf_path = temp_dir / "test_rulebook.pdf"
    # Create a simple PDF-like file (not a real PDF, but good enough for path testing)
    pdf_path.write_bytes(b"%PDF-1.4\n%Test PDF content\n")
    return pdf_path


# Test utilities
class QdrantMock:
    """Mock Qdrant client for testing without a real instance."""
    
    def __init__(self):
        self.collections = {}
        self.points = {}
        
    def get_collections(self):
        from types import SimpleNamespace
        return SimpleNamespace(collections=[
            SimpleNamespace(name=name) for name in self.collections.keys()
        ])
        
    def create_collection(self, collection_name, vectors_config):
        self.collections[collection_name] = {
            "config": vectors_config,
            "points": []
        }
        
    def delete_collection(self, collection_name):
        if collection_name in self.collections:
            del self.collections[collection_name]
            
    def upsert(self, collection_name, points):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        self.collections[collection_name]["points"].extend(points)
        
    def search(self, collection_name, query_vector, limit, **kwargs):
        if collection_name not in self.collections:
            return []
        # Simple mock search - return some points
        from types import SimpleNamespace
        results = []
        for i, point in enumerate(self.collections[collection_name]["points"][:limit]):
            results.append(SimpleNamespace(
                score=0.9 - (i * 0.1),
                payload=point.payload if hasattr(point, 'payload') else {}
            ))
        return results
        
    def get_collection(self, collection_name):
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
        from types import SimpleNamespace
        return SimpleNamespace(
            vectors_count=len(self.collections[collection_name]["points"]),
            indexed_vectors_count=len(self.collections[collection_name]["points"]),
            status="ready",
            config=SimpleNamespace(
                params=SimpleNamespace(
                    vectors=SimpleNamespace(
                        size=384,
                        distance="Cosine"
                    )
                )
            )
        )


@pytest.fixture
def mock_qdrant_client(monkeypatch):
    """Mock Qdrant client for tests."""
    mock_client = QdrantMock()
    
    def mock_init(self, *args, **kwargs):
        self.get_collections = mock_client.get_collections
        self.create_collection = mock_client.create_collection
        self.delete_collection = mock_client.delete_collection
        self.upsert = mock_client.upsert
        self.search = mock_client.search
        self.get_collection = mock_client.get_collection
        
    from qdrant_client import QdrantClient
    monkeypatch.setattr(QdrantClient, "__init__", mock_init)
    
    return mock_client 