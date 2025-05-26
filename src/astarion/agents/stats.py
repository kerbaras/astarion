"""Stats agent for ability score generation."""

import random
from typing import Dict, List, Any, Optional
from enum import Enum

from loguru import logger

from astarion.models.character import AbilityScores


class GenerationMethod(str, Enum):
    """Ability score generation methods."""
    STANDARD_ARRAY = "standard_array"
    POINT_BUY = "point_buy"
    ROLLING = "rolling"
    MANUAL = "manual"


class StatsAgent:
    """Agent responsible for generating and managing ability scores."""
    
    # Standard array values for D&D 5e
    STANDARD_ARRAY = [15, 14, 13, 12, 10, 8]
    
    # Point buy costs for D&D 5e
    POINT_BUY_COSTS = {
        8: 0, 9: 1, 10: 2, 11: 3, 12: 4, 13: 5, 14: 7, 15: 9
    }
    POINT_BUY_BUDGET = 27
    
    def generate_ability_scores(
        self,
        method: str = "standard_array",
        preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, int]:
        """Generate ability scores based on the chosen method."""
        logger.info(f"Generating ability scores using method: {method}")
        
        if method == GenerationMethod.STANDARD_ARRAY:
            return self._generate_standard_array(preferences)
        elif method == GenerationMethod.POINT_BUY:
            return self._generate_point_buy(preferences)
        elif method == GenerationMethod.ROLLING:
            return self._generate_rolling(preferences)
        elif method == GenerationMethod.MANUAL:
            return self._generate_manual(preferences)
        else:
            logger.warning(f"Unknown generation method: {method}, using standard array")
            return self._generate_standard_array(preferences)
    
    def _generate_standard_array(self, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Generate ability scores using standard array."""
        abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        scores = self.STANDARD_ARRAY.copy()
        
        # If preferences specify priority abilities, assign higher scores to them
        if preferences and "priority_abilities" in preferences:
            priority = preferences["priority_abilities"]
            # Sort scores descending
            scores.sort(reverse=True)
            
            result = {}
            for i, ability in enumerate(priority[:len(scores)]):
                if ability in abilities:
                    result[ability] = scores[i]
                    abilities.remove(ability)
            
            # Assign remaining scores to remaining abilities
            remaining_scores = scores[len(result):]
            random.shuffle(remaining_scores)
            for ability, score in zip(abilities, remaining_scores):
                result[ability] = score
                
            # Ensure all abilities have scores
            for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
                if ability not in result:
                    result[ability] = 10
                    
            return result
        else:
            # Random assignment
            random.shuffle(scores)
            return {
                "strength": scores[0],
                "dexterity": scores[1],
                "constitution": scores[2],
                "intelligence": scores[3],
                "wisdom": scores[4],
                "charisma": scores[5],
            }
    
    def _generate_point_buy(self, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Generate ability scores using point buy system."""
        # Start with all scores at 8
        scores = {
            "strength": 8,
            "dexterity": 8,
            "constitution": 8,
            "intelligence": 8,
            "wisdom": 8,
            "charisma": 8,
        }
        
        remaining_points = self.POINT_BUY_BUDGET
        
        # If preferences specify priority abilities, invest more in them
        if preferences and "priority_abilities" in preferences:
            priority = preferences["priority_abilities"]
            
            # First pass: Try to get priority abilities to 15
            for ability in priority:
                if ability in scores and remaining_points >= 9:  # Cost to go from 8 to 15
                    scores[ability] = 15
                    remaining_points -= 9
            
            # Second pass: Distribute remaining points
            abilities = [a for a in scores.keys() if scores[a] < 15]
            while remaining_points > 0 and abilities:
                for ability in abilities:
                    if scores[ability] < 15:
                        next_score = scores[ability] + 1
                        if next_score in self.POINT_BUY_COSTS:
                            cost = self.POINT_BUY_COSTS[next_score] - self.POINT_BUY_COSTS[scores[ability]]
                            if cost <= remaining_points:
                                scores[ability] = next_score
                                remaining_points -= cost
                                if scores[ability] >= 15:
                                    abilities.remove(ability)
                                break
                else:
                    # No more improvements possible
                    break
        else:
            # Balanced distribution
            target_score = 13  # Try to get all scores to 13 if possible
            for ability in scores:
                while scores[ability] < target_score and remaining_points > 0:
                    next_score = scores[ability] + 1
                    if next_score in self.POINT_BUY_COSTS:
                        cost = self.POINT_BUY_COSTS[next_score] - self.POINT_BUY_COSTS[scores[ability]]
                        if cost <= remaining_points:
                            scores[ability] = next_score
                            remaining_points -= cost
                        else:
                            break
                    else:
                        break
        
        return scores
    
    def _generate_rolling(self, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Generate ability scores by rolling dice (4d6 drop lowest)."""
        def roll_ability() -> int:
            """Roll 4d6 and drop the lowest."""
            rolls = [random.randint(1, 6) for _ in range(4)]
            rolls.sort(reverse=True)
            return sum(rolls[:3])
        
        # Roll 6 scores
        rolled_scores = [roll_ability() for _ in range(6)]
        rolled_scores.sort(reverse=True)
        
        abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        
        # Assign based on preferences
        if preferences and "priority_abilities" in preferences:
            priority = preferences["priority_abilities"]
            result = {}
            
            # Assign best scores to priority abilities
            for i, ability in enumerate(priority[:6]):
                if ability in abilities:
                    result[ability] = rolled_scores[i]
                    abilities.remove(ability)
            
            # Assign remaining scores
            remaining_scores = rolled_scores[len(result):]
            random.shuffle(remaining_scores)
            for ability, score in zip(abilities, remaining_scores):
                result[ability] = score
                
            # Ensure all abilities have scores
            for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
                if ability not in result:
                    result[ability] = 10
                    
            return result
        else:
            # Random assignment
            random.shuffle(rolled_scores)
            return {
                "strength": rolled_scores[0],
                "dexterity": rolled_scores[1],
                "constitution": rolled_scores[2],
                "intelligence": rolled_scores[3],
                "wisdom": rolled_scores[4],
                "charisma": rolled_scores[5],
            }
    
    def _generate_manual(self, preferences: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """Use manually specified ability scores."""
        if not preferences or "manual_scores" not in preferences:
            logger.warning("No manual scores provided, using standard array")
            return self._generate_standard_array(preferences)
        
        manual_scores = preferences["manual_scores"]
        
        # Validate and ensure all abilities are present
        result = {}
        for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            if ability in manual_scores:
                score = manual_scores[ability]
                # Clamp to valid range
                result[ability] = max(1, min(30, int(score)))
            else:
                result[ability] = 10  # Default score
                
        return result
    
    def optimize_scores_for_class(
        self,
        scores: Dict[str, int],
        class_name: str,
        allow_reallocation: bool = True
    ) -> Dict[str, int]:
        """Optimize ability scores for a specific class."""
        # Define optimal ability priorities by class
        class_priorities = {
            "Fighter": ["strength", "constitution", "dexterity"],
            "Wizard": ["intelligence", "constitution", "dexterity"],
            "Cleric": ["wisdom", "constitution", "strength"],
            "Rogue": ["dexterity", "intelligence", "constitution"],
            "Ranger": ["dexterity", "wisdom", "constitution"],
            "Paladin": ["strength", "charisma", "constitution"],
            "Barbarian": ["strength", "constitution", "dexterity"],
            "Sorcerer": ["charisma", "constitution", "dexterity"],
            "Warlock": ["charisma", "constitution", "dexterity"],
            "Bard": ["charisma", "dexterity", "constitution"],
            "Druid": ["wisdom", "constitution", "dexterity"],
            "Monk": ["dexterity", "wisdom", "constitution"],
        }
        
        if not allow_reallocation or class_name not in class_priorities:
            return scores
            
        # Get current scores as a list
        current_scores = list(scores.values())
        current_scores.sort(reverse=True)
        
        # Reassign based on class priorities
        priorities = class_priorities[class_name]
        all_abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        remaining_abilities = [a for a in all_abilities if a not in priorities]
        
        result = {}
        
        # Assign best scores to priority abilities
        for i, ability in enumerate(priorities[:len(current_scores)]):
            result[ability] = current_scores[i]
            
        # Assign remaining scores to remaining abilities
        remaining_scores = current_scores[len(priorities):]
        for ability, score in zip(remaining_abilities, remaining_scores):
            result[ability] = score
            
        return result
    
    def validate_scores(self, scores: Dict[str, int]) -> bool:
        """Validate that ability scores are within legal ranges."""
        try:
            ability_scores = AbilityScores(**scores)
            return True
        except Exception as e:
            logger.error(f"Invalid ability scores: {e}")
            return False 