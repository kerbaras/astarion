"""Tests for agent functionality."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from astarion.agents.base import BaseAgent
from astarion.agents.stats import StatsAgent
from astarion.agents.validation import ValidationAgent
from astarion.agents.ruleset import RulesetAgent, RuleResult
from astarion.models.character import GameSystem
from astarion.models.validation import ValidationResult, ValidationError
from astarion.rag.extractor import ContentType


class TestBaseAgent:
    """Test suite for base agent."""
    
    def test_base_agent_metadata(self):
        """Test agent metadata."""
        agent = BaseAgent("TestAgent", "Test description")
        
        assert agent.metadata.name == "TestAgent"
        assert agent.metadata.description == "Test description"
        assert agent.metadata.version == "1.0.0"
        assert agent.metadata.capabilities == []
        
    def test_add_capability(self):
        """Test adding capabilities."""
        agent = BaseAgent("TestAgent", "Test")
        
        agent.add_capability("test_capability")
        assert "test_capability" in agent.metadata.capabilities
        
        # Should not add duplicates
        agent.add_capability("test_capability")
        assert agent.metadata.capabilities.count("test_capability") == 1
        
    @pytest.mark.asyncio
    async def test_process_not_implemented(self):
        """Test that process method must be implemented."""
        agent = BaseAgent("TestAgent", "Test")
        
        with pytest.raises(NotImplementedError):
            await agent.process()


class TestStatsAgent:
    """Test suite for stats agent."""
    
    def test_stats_agent_init(self):
        """Test stats agent initialization."""
        agent = StatsAgent()
        assert agent.metadata.name == "StatsAgent"
        assert "generate" in agent.metadata.description.lower()
        
    def test_generate_standard_array(self):
        """Test standard array generation."""
        agent = StatsAgent()
        scores = agent.generate_ability_scores("standard_array")
        
        # Should return standard array values
        values = sorted(scores.values())
        assert values == [8, 10, 12, 13, 14, 15]
        
    def test_generate_point_buy(self):
        """Test point buy generation."""
        agent = StatsAgent()
        scores = agent.generate_ability_scores("point_buy")
        
        # All scores should be between 8 and 15
        for score in scores.values():
            assert 8 <= score <= 15
            
    def test_generate_rolling(self):
        """Test rolling method generation."""
        agent = StatsAgent()
        scores = agent.generate_ability_scores("rolling")
        
        # All scores should be between 3 and 18
        for score in scores.values():
            assert 3 <= score <= 18
            
    def test_generate_with_preferences(self):
        """Test generation with preferences."""
        agent = StatsAgent()
        preferences = {
            "prioritize": ["strength", "constitution"],
            "minimize": ["intelligence"]
        }
        
        scores = agent.generate_ability_scores("standard_array", preferences)
        
        # Prioritized scores should be higher
        assert scores["strength"] >= scores["intelligence"]
        assert scores["constitution"] >= scores["intelligence"]
        
    def test_optimize_for_class(self):
        """Test optimization for specific classes."""
        agent = StatsAgent()
        
        # Fighter optimization
        fighter_scores = agent.optimize_for_class("Fighter", "standard_array")
        assert fighter_scores["strength"] >= 14
        
        # Wizard optimization
        wizard_scores = agent.optimize_for_class("Wizard", "standard_array")
        assert wizard_scores["intelligence"] >= 14
        
    def test_roll_4d6_drop_lowest(self):
        """Test the 4d6 drop lowest method."""
        agent = StatsAgent()
        
        for _ in range(100):  # Test multiple times
            score = agent._roll_4d6_drop_lowest()
            assert 3 <= score <= 18
            
    def test_calculate_point_cost(self):
        """Test point buy cost calculation."""
        agent = StatsAgent()
        
        assert agent._calculate_point_cost(8) == 0
        assert agent._calculate_point_cost(13) == 5
        assert agent._calculate_point_cost(14) == 7
        assert agent._calculate_point_cost(15) == 9


class TestValidationAgent:
    """Test suite for validation agent."""
    
    def test_validation_agent_init(self):
        """Test validation agent initialization."""
        agent = ValidationAgent()
        assert agent.metadata.name == "ValidationAgent"
        
    @pytest.mark.asyncio
    async def test_validate_character_valid(self, sample_character):
        """Test validating a valid character."""
        agent = ValidationAgent()
        
        result = await agent.validate(sample_character)
        
        assert isinstance(result, ValidationResult)
        assert result.character_name == "Test Hero"
        assert result.character_level == 1
        
    @pytest.mark.asyncio
    async def test_validate_ability_scores(self, sample_character):
        """Test ability score validation."""
        agent = ValidationAgent()
        
        # Test with invalid scores
        sample_character.ability_scores.strength = 25  # Too high
        errors = agent._validate_ability_scores(sample_character)
        
        assert len(errors) > 0
        assert any("ability score" in e.message.lower() for e in errors)
        
    def test_validate_class_requirements(self, sample_character):
        """Test class requirement validation."""
        agent = ValidationAgent()
        
        # Fighter has no special requirements in basic rules
        errors = agent._validate_class_requirements(sample_character)
        assert len(errors) == 0
        
        # Test with a class that has requirements
        sample_character.classes[0].name = "Paladin"
        errors = agent._validate_class_requirements(sample_character)
        # Might have alignment or ability requirements
        
    def test_validate_equipment(self, sample_character):
        """Test equipment validation."""
        agent = ValidationAgent()
        
        errors = agent._validate_equipment(sample_character)
        # Basic validation should pass
        assert isinstance(errors, list)


class TestRulesetAgent:
    """Test suite for ruleset agent."""
    
    @pytest.mark.asyncio
    async def test_ruleset_agent_init(self):
        """Test ruleset agent initialization."""
        agent = RulesetAgent()
        assert agent.metadata.name == "RulesetAgent"
        assert agent.processor is not None
        
    @pytest.mark.asyncio
    async def test_query_rules(self, monkeypatch):
        """Test querying rules."""
        agent = RulesetAgent()
        
        # Mock the processor search
        mock_results = [
            {
                "text": "Fireball spell text",
                "citation": "PHB, p. 241",
                "score": 0.9,
                "metadata": {"chunk_type": "spell", "page_number": 241}
            }
        ]
        
        agent.processor.search = AsyncMock(return_value=mock_results)
        
        results = await agent.query_rules(
            "fireball",
            GameSystem.DND5E,
            limit=5
        )
        
        assert len(results) == 1
        assert isinstance(results[0], RuleResult)
        assert "Fireball" in results[0].text
        assert results[0].citation == "PHB, p. 241"
        
    @pytest.mark.asyncio
    async def test_find_spell(self, monkeypatch):
        """Test finding a specific spell."""
        agent = RulesetAgent()
        
        mock_results = [
            {
                "text": "Fireball\n3rd-level evocation",
                "citation": "PHB, p. 241",
                "score": 0.95,
                "metadata": {"chunk_type": "spell"}
            }
        ]
        
        agent.processor.search = AsyncMock(return_value=mock_results)
        
        spell = await agent.find_spell("fireball")
        
        assert spell is not None
        assert "fireball" in spell.text.lower()
        
    @pytest.mark.asyncio
    async def test_find_feat(self, monkeypatch):
        """Test finding a specific feat."""
        agent = RulesetAgent()
        
        mock_results = [
            {
                "text": "Great Weapon Master\nPrerequisite: None",
                "citation": "PHB, p. 167",
                "score": 0.9,
                "metadata": {"chunk_type": "feat"}
            }
        ]
        
        agent.processor.search = AsyncMock(return_value=mock_results)
        
        feat = await agent.find_feat("Great Weapon Master")
        
        assert feat is not None
        assert "great weapon master" in feat.text.lower()
        
    @pytest.mark.asyncio
    async def test_check_prerequisite(self, monkeypatch):
        """Test checking prerequisites."""
        agent = RulesetAgent()
        
        mock_results = [
            {
                "text": "Sharpshooter\nPrerequisite: Dexterity 13 or higher",
                "citation": "PHB",
                "score": 0.9,
                "metadata": {}
            }
        ]
        
        agent.processor.search = AsyncMock(return_value=mock_results)
        
        prereq = await agent.check_prerequisite("Sharpshooter")
        
        assert prereq is not None
        assert "Dexterity 13" in prereq
        
    @pytest.mark.asyncio
    async def test_get_class_features(self, monkeypatch):
        """Test getting class features."""
        agent = RulesetAgent()
        
        mock_results = [
            {
                "text": "Action Surge\nStarting at 2nd level, you can push yourself",
                "citation": "PHB",
                "score": 0.9,
                "metadata": {"chunk_type": "class_feature"}
            }
        ]
        
        agent.processor.search = AsyncMock(return_value=mock_results)
        
        features = await agent.get_class_features("Fighter", level=2)
        
        assert len(features) > 0
        assert any("2nd level" in f.text for f in features)
        
    def test_analyze_conflicts(self):
        """Test conflict analysis."""
        agent = RulesetAgent()
        
        rule1_results = [
            RuleResult(
                text="You cannot wear armor",
                citation="PHB",
                relevance_score=0.9
            )
        ]
        
        rule2_results = [
            RuleResult(
                text="You must wear heavy armor",
                citation="PHB",
                relevance_score=0.9
            )
        ]
        
        conflicts = agent._analyze_conflicts(rule1_results, rule2_results)
        
        assert len(conflicts) > 0
        assert any("cannot vs must" in c for c in conflicts)
        
    def test_create_rule_source(self):
        """Test creating rule source from result."""
        agent = RulesetAgent()
        
        rule_result = RuleResult(
            text="Test rule text that is very long " * 20,
            citation="PHB, p. 42",
            relevance_score=0.9,
            page_number=42,
            rule_type="spell"
        )
        
        source = agent.create_rule_source(rule_result)
        
        assert source.book == "PHB"
        assert source.page == 42
        assert source.section == "spell"
        assert len(source.rule_text) <= 203  # 200 + "..." 