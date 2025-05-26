"""Basic workflow tests for Astarion."""

import pytest
import json
from pathlib import Path

from astarion.models.character import Character, GameSystem, AbilityScores, Race, CharacterClass, Background, Equipment
from astarion.models.validation import ValidationResult
from astarion.agents.stats import StatsAgent
from astarion.agents.validation import ValidationAgent
from astarion.core.orchestrator import CharacterCreationOrchestrator


def test_character_model_creation():
    """Test creating a character model."""
    character = Character(
        name="Test Hero",
        system=GameSystem.DND5E,
        level=1,
        race=Race(name="Human", ability_bonuses={"strength": 1}),
        classes=[CharacterClass(
            name="Fighter", 
            level=1, 
            hit_dice="d10",
            primary_ability="strength",
            saving_throws=["strength", "constitution"]
        )],
        background=Background(name="Soldier", skills=["Athletics", "Intimidation"]),
        ability_scores=AbilityScores(
            strength=15, dexterity=14, constitution=13, 
            intelligence=12, wisdom=10, charisma=8
        ),
        hit_points=10,
        max_hit_points=10,
        armor_class=16,
        proficiency_bonus=2,
        equipment=Equipment()
    )
    
    assert character.name == "Test Hero"
    assert character.level == 1
    assert character.get_ability_modifier("strength") == 3  # 15 + 1 racial = 16, modifier = 3


def test_stats_agent_standard_array():
    """Test the stats agent generating standard array scores."""
    agent = StatsAgent()
    
    # Generate with standard array
    scores = agent.generate_ability_scores(method="standard_array")
    
    # Check all abilities are present
    assert set(scores.keys()) == {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}
    
    # Check values are from standard array
    values = sorted(scores.values())
    assert values == [8, 10, 12, 13, 14, 15]


def test_stats_agent_point_buy():
    """Test the stats agent with point buy."""
    agent = StatsAgent()
    
    # Generate with point buy
    scores = agent.generate_ability_scores(
        method="point_buy",
        preferences={"priority_abilities": ["strength", "constitution"]}
    )
    
    # Check priority abilities got higher scores
    assert scores["strength"] >= 13
    assert scores["constitution"] >= 13
    
    # Check all scores are valid for point buy
    for score in scores.values():
        assert 8 <= score <= 15


def test_validation_agent():
    """Test the validation agent."""
    # Load test character
    test_char_path = Path("tests/test_character.json")
    if test_char_path.exists():
        with open(test_char_path) as f:
            char_data = json.load(f)
        character = Character.from_dict(char_data)
    else:
        # Create a simple test character
        character = Character(
            name="Test Fighter",
            system=GameSystem.DND5E,
            level=1,
            race=Race(name="Human"),
            classes=[CharacterClass(name="Fighter", level=1, hit_dice="d10", 
                                  primary_ability="strength", saving_throws=["strength", "constitution"])],
            background=Background(name="Soldier"),
            ability_scores=AbilityScores(strength=16, dexterity=14, constitution=15,
                                       intelligence=10, wisdom=13, charisma=12),
            hit_points=12,
            max_hit_points=12,
            armor_class=16,
            proficiency_bonus=2,
            equipment=Equipment(armor="Chain mail", shield=True)
        )
    
    # Validate
    agent = ValidationAgent()
    result = agent.validate(character, GameSystem.DND5E, strict_mode=True)
    
    # Check result
    assert isinstance(result, ValidationResult)
    assert result.character_name == character.name
    assert result.rules_checked > 0
    
    # Print validation report for debugging
    print(result.to_report())


@pytest.mark.asyncio
async def test_character_creation_orchestrator():
    """Test the character creation orchestrator."""
    orchestrator = CharacterCreationOrchestrator()
    
    # Create a character
    result = await orchestrator.create_character(
        user_preferences={
            "name": "Aragorn",
            "race": "Human", 
            "class": "Ranger",
            "level": 1,
            "generation_method": "standard_array",
            "priority_abilities": ["dexterity", "wisdom"]
        },
        system=GameSystem.DND5E
    )
    
    # Check result
    assert result["is_complete"]
    assert not result.get("errors")
    assert result["character"]["name"] == "Aragorn"
    assert result["character"]["race"]["name"] == "Human"
    assert result["character"]["classes"][0]["name"] == "Ranger"
    
    # Check processing history
    assert len(result["processing_history"]) > 0
    assert "Character creation completed successfully" in result["processing_history"]


if __name__ == "__main__":
    # Run tests directly
    test_character_model_creation()
    test_stats_agent_standard_array()
    test_stats_agent_point_buy()
    test_validation_agent()
    
    # Run async test
    import asyncio
    asyncio.run(test_character_creation_orchestrator())
    
    print("All tests passed!") 