"""Character validator wrapper for external API."""

from typing import Dict, Any, Optional
from loguru import logger

from astarion.models.character import Character, GameSystem
from astarion.models.validation import ValidationResult
from astarion.agents.validation import ValidationAgent


class CharacterValidator:
    """Main character validation interface."""
    
    def __init__(self, system: str = "dnd5e"):
        """Initialize the validator for a specific game system."""
        self.system = GameSystem(system)
        self.validation_agent = ValidationAgent()
        
    async def validate_character(
        self,
        character_data: Dict[str, Any],
        strict_mode: bool = True
    ) -> ValidationResult:
        """Validate a character from dictionary data."""
        try:
            # Convert dictionary to Character model
            character = Character.from_dict(character_data)
            
            # Validate using the agent
            result = self.validation_agent.validate(
                character=character,
                system=self.system,
                strict_mode=strict_mode
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            # Return a validation result with the error
            return ValidationResult(
                is_valid=False,
                character_name=character_data.get("name", "Unknown"),
                game_system=self.system.value,
                validation_time=0.0,
                rules_checked=0,
                errors=[{
                    "rule_id": "validation_error",
                    "message": f"Failed to validate character: {str(e)}",
                    "field": None,
                    "source": None
                }]
            )
            
    def validate_character_sync(
        self,
        character_data: Dict[str, Any],
        strict_mode: bool = True
    ) -> ValidationResult:
        """Synchronous version of validate_character."""
        try:
            character = Character.from_dict(character_data)
            return self.validation_agent.validate(
                character=character,
                system=self.system,
                strict_mode=strict_mode
            )
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return ValidationResult(
                is_valid=False,
                character_name=character_data.get("name", "Unknown"),
                game_system=self.system.value,
                validation_time=0.0,
                rules_checked=0
            ) 