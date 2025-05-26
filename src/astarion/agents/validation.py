"""Validation agent for character rule checking."""

from typing import Dict, Any, List, Optional
from loguru import logger

from astarion.models.character import Character, GameSystem
from astarion.models.validation import (
    ValidationResult, ValidationError, ValidationWarning, 
    ValidationInfo, RuleSource, OptimizationSuggestion
)


class ValidationAgent:
    """Agent responsible for validating character builds against game rules."""
    
    def __init__(self):
        """Initialize the validation agent."""
        # TODO: Load rule sets from database or MCP servers
        self.rule_sets = {}
        
    def validate(
        self,
        character: Character,
        system: GameSystem,
        strict_mode: bool = True
    ) -> ValidationResult:
        """Validate a character against the rules of a game system."""
        logger.info(f"Validating character '{character.name}' for {system}")
        
        result = ValidationResult(
            is_valid=True,
            character_name=character.name,
            game_system=system,
            validation_time=0.0,
            rules_checked=0
        )
        
        # Run various validation checks
        self._validate_ability_scores(character, result)
        self._validate_race(character, result)
        self._validate_class(character, result)
        self._validate_multiclass(character, result, strict_mode)
        self._validate_skills(character, result)
        self._validate_equipment(character, result)
        
        # Add optimization suggestions if the character is valid
        if result.is_valid:
            self._generate_optimization_suggestions(character, result)
            
        logger.info(f"Validation complete: {'VALID' if result.is_valid else 'INVALID'}")
        return result
        
    def _validate_ability_scores(self, character: Character, result: ValidationResult) -> None:
        """Validate ability scores are within legal ranges."""
        result.rules_checked += 1
        
        # Check each ability score
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            score = getattr(character.ability_scores, ability)
            
            if score < 1 or score > 30:
                result.add_error(ValidationError(
                    rule_id="ability_score_range",
                    message=f"{ability.capitalize()} score of {score} is outside valid range (1-30)",
                    field=f"ability_scores.{ability}",
                    source=RuleSource(book="PHB", page=12, section="Ability Scores"),
                    fix_suggestion=f"Set {ability} to a value between 1 and 30"
                ))
                
        # Check for standard array/point buy validity if using those methods
        if character.creation_method == "standard_array":
            self._validate_standard_array(character, result)
        elif character.creation_method == "point_buy":
            self._validate_point_buy(character, result)
            
    def _validate_standard_array(self, character: Character, result: ValidationResult) -> None:
        """Validate that ability scores match standard array."""
        result.rules_checked += 1
        
        standard_array = [15, 14, 13, 12, 10, 8]
        scores = [
            character.ability_scores.strength,
            character.ability_scores.dexterity,
            character.ability_scores.constitution,
            character.ability_scores.intelligence,
            character.ability_scores.wisdom,
            character.ability_scores.charisma
        ]
        
        # Account for racial bonuses
        # TODO: Properly subtract racial bonuses
        
        scores_sorted = sorted(scores, reverse=True)
        standard_sorted = sorted(standard_array, reverse=True)
        
        # For now, just check if the total is reasonable
        if sum(scores) > sum(standard_array) + 10:  # Allow some racial bonuses
            result.add_warning(ValidationWarning(
                rule_id="standard_array_exceeded",
                message="Ability scores appear higher than standard array allows",
                field="ability_scores",
                source=RuleSource(book="PHB", page=13, section="Standard Array"),
                optimization_suggestion="Verify racial bonuses are correctly applied"
            ))
            
    def _validate_point_buy(self, character: Character, result: ValidationResult) -> None:
        """Validate that ability scores follow point buy rules."""
        result.rules_checked += 1
        
        # Point buy validation
        # TODO: Implement full point buy calculation
        pass
        
    def _validate_race(self, character: Character, result: ValidationResult) -> None:
        """Validate race selection and features."""
        result.rules_checked += 1
        
        # Check if race is valid
        valid_races = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn", "Gnome", "Half-Elf", "Half-Orc", "Tiefling"]
        
        if character.race.name not in valid_races:
            if character.system == GameSystem.DND5E:
                result.add_warning(ValidationWarning(
                    rule_id="unknown_race",
                    message=f"Race '{character.race.name}' is not in the core rules",
                    field="race.name",
                    source=RuleSource(book="PHB", page=17, section="Races"),
                    optimization_suggestion="Ensure this race is from an official supplement or approved homebrew"
                ))
                
    def _validate_class(self, character: Character, result: ValidationResult) -> None:
        """Validate class selection and prerequisites."""
        result.rules_checked += 1
        
        # Check each class
        for char_class in character.classes:
            # Validate class exists
            valid_classes = ["Barbarian", "Bard", "Cleric", "Druid", "Fighter", "Monk", 
                           "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"]
            
            if char_class.name not in valid_classes:
                result.add_warning(ValidationWarning(
                    rule_id="unknown_class",
                    message=f"Class '{char_class.name}' is not in the core rules",
                    field="classes",
                    source=RuleSource(book="PHB", page=45, section="Classes")
                ))
                
            # Check hit dice
            expected_hit_dice = {
                "Barbarian": "d12", "Fighter": "d10", "Paladin": "d10", "Ranger": "d10",
                "Bard": "d8", "Cleric": "d8", "Druid": "d8", "Monk": "d8", "Rogue": "d8", "Warlock": "d8",
                "Sorcerer": "d6", "Wizard": "d6"
            }
            
            if char_class.name in expected_hit_dice and char_class.hit_dice != expected_hit_dice[char_class.name]:
                result.add_error(ValidationError(
                    rule_id="incorrect_hit_dice",
                    message=f"{char_class.name} should have {expected_hit_dice[char_class.name]} hit dice, not {char_class.hit_dice}",
                    field="classes.hit_dice",
                    source=RuleSource(book="PHB", page=45, section=char_class.name)
                ))
                
    def _validate_multiclass(self, character: Character, result: ValidationResult, strict_mode: bool) -> None:
        """Validate multiclass prerequisites."""
        if len(character.classes) <= 1:
            return
            
        result.rules_checked += 1
        
        # Multiclass prerequisites for D&D 5e
        multiclass_requirements = {
            "Barbarian": {"strength": 13},
            "Bard": {"charisma": 13},
            "Cleric": {"wisdom": 13},
            "Druid": {"wisdom": 13},
            "Fighter": {"strength": 13, "dexterity": 13},  # OR, not AND
            "Monk": {"dexterity": 13, "wisdom": 13},
            "Paladin": {"strength": 13, "charisma": 13},
            "Ranger": {"dexterity": 13, "wisdom": 13},
            "Rogue": {"dexterity": 13},
            "Sorcerer": {"charisma": 13},
            "Warlock": {"charisma": 13},
            "Wizard": {"intelligence": 13}
        }
        
        for char_class in character.classes:
            if char_class.name in multiclass_requirements:
                requirements = multiclass_requirements[char_class.name]
                
                # Special case for Fighter (STR or DEX)
                if char_class.name == "Fighter":
                    str_score = character.get_total_ability_score("strength")
                    dex_score = character.get_total_ability_score("dexterity")
                    
                    if str_score < 13 and dex_score < 13:
                        result.add_error(ValidationError(
                            rule_id="multiclass_prerequisite",
                            message=f"Fighter multiclass requires Strength 13 OR Dexterity 13",
                            field="classes",
                            source=RuleSource(book="PHB", page=163, section="Multiclassing Prerequisites"),
                            fix_suggestion="Increase Strength or Dexterity to at least 13"
                        ))
                else:
                    # Check all requirements
                    for ability, min_score in requirements.items():
                        actual_score = character.get_total_ability_score(ability)
                        if actual_score < min_score:
                            result.add_error(ValidationError(
                                rule_id="multiclass_prerequisite",
                                message=f"{char_class.name} multiclass requires {ability.capitalize()} {min_score}, but character has {actual_score}",
                                field="classes",
                                source=RuleSource(book="PHB", page=163, section="Multiclassing Prerequisites"),
                                fix_suggestion=f"Increase {ability.capitalize()} to at least {min_score}"
                            ))
                            
    def _validate_skills(self, character: Character, result: ValidationResult) -> None:
        """Validate skill proficiency selections."""
        result.rules_checked += 1
        
        # TODO: Implement skill validation
        # Check number of skills based on class + background
        # Verify skills are valid choices
        pass
        
    def _validate_equipment(self, character: Character, result: ValidationResult) -> None:
        """Validate equipment and proficiencies."""
        result.rules_checked += 1
        
        # Check armor proficiency
        if character.equipment.armor:
            armor_type = self._get_armor_type(character.equipment.armor)
            if armor_type and not self._has_armor_proficiency(character, armor_type):
                result.add_warning(ValidationWarning(
                    rule_id="armor_proficiency",
                    message=f"Character lacks proficiency with {armor_type} armor ({character.equipment.armor})",
                    field="equipment.armor",
                    source=RuleSource(book="PHB", page=144, section="Armor Proficiency"),
                    optimization_suggestion="Consider choosing armor you're proficient with or gaining proficiency through class/feat"
                ))
                
    def _get_armor_type(self, armor: str) -> Optional[str]:
        """Determine armor type category."""
        light_armor = ["padded", "leather", "studded leather"]
        medium_armor = ["hide", "chain shirt", "scale mail", "breastplate", "half plate"]
        heavy_armor = ["ring mail", "chain mail", "splint", "plate"]
        
        armor_lower = armor.lower()
        if any(a in armor_lower for a in light_armor):
            return "light"
        elif any(a in armor_lower for a in medium_armor):
            return "medium"
        elif any(a in armor_lower for a in heavy_armor):
            return "heavy"
        return None
        
    def _has_armor_proficiency(self, character: Character, armor_type: str) -> bool:
        """Check if character has proficiency with armor type."""
        # Simplified check - in reality would check class features
        class_armor_proficiencies = {
            "Fighter": ["light", "medium", "heavy", "shields"],
            "Paladin": ["light", "medium", "heavy", "shields"],
            "Cleric": ["light", "medium", "shields"],
            "Ranger": ["light", "medium", "shields"],
            "Barbarian": ["light", "medium", "shields"],
            "Bard": ["light"],
            "Rogue": ["light"],
            "Warlock": ["light"],
            "Druid": ["light", "medium", "shields"],  # Non-metal restriction
            "Monk": [],
            "Sorcerer": [],
            "Wizard": []
        }
        
        for char_class in character.classes:
            if char_class.name in class_armor_proficiencies:
                if armor_type in class_armor_proficiencies[char_class.name]:
                    return True
        return False
        
    def _generate_optimization_suggestions(self, character: Character, result: ValidationResult) -> None:
        """Generate optimization suggestions for the character build."""
        # Simple optimization suggestions
        primary_class = character.classes[0] if character.classes else None
        
        if primary_class:
            # Suggest ability score improvements
            ability_priorities = {
                "Fighter": "strength",
                "Wizard": "intelligence", 
                "Cleric": "wisdom",
                "Rogue": "dexterity"
            }
            
            if primary_class.name in ability_priorities:
                primary_ability = ability_priorities[primary_class.name]
                current_score = character.get_total_ability_score(primary_ability)
                
                if current_score < 16:
                    result.add_optimization(OptimizationSuggestion(
                        category="ability_scores",
                        current_value=current_score,
                        suggested_value="16+",
                        impact=f"Increases {primary_class.name} effectiveness significantly",
                        reasoning=f"{primary_ability.capitalize()} is the primary ability for {primary_class.name}",
                        sources=[RuleSource(book="PHB", page=45, section="Class Features")],
                        priority=1
                    )) 