"""LangGraph orchestrator for character creation workflow."""

import time
from typing import Dict, Any, List, Optional, TypedDict, Annotated
from enum import Enum

from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field
from loguru import logger

from astarion.models.character import Character, GameSystem
from astarion.models.validation import ValidationResult, ValidationError, RuleSource
from astarion.agents.stats import StatsAgent
from astarion.agents.validation import ValidationAgent


class ProcessingStage(str, Enum):
    """Character creation processing stages."""
    INITIAL = "initial"
    STATS_GENERATION = "stats_generation"
    RACE_SELECTION = "race_selection"
    CLASS_SELECTION = "class_selection"
    BACKGROUND_CREATION = "background_creation"
    EQUIPMENT_SELECTION = "equipment_selection"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"
    COMPLETE = "complete"
    ERROR = "error"


class CharacterState(TypedDict):
    """State for character creation workflow."""
    # Current processing stage
    stage: ProcessingStage
    
    # Character data being built
    character_data: Dict[str, Any]
    
    # User preferences
    user_preferences: Dict[str, Any]
    system: GameSystem
    optimization_goals: List[str]
    
    # Processing metadata
    validation_results: Optional[ValidationResult]
    errors: List[str]
    warnings: List[str]
    processing_history: List[str]
    
    # Control flow
    retry_count: int
    should_optimize: bool
    is_complete: bool


class CharacterCreationOrchestrator:
    """Orchestrates the character creation workflow using LangGraph."""
    
    def __init__(self):
        """Initialize the orchestrator."""
        self.stats_agent = StatsAgent()
        self.validation_agent = ValidationAgent()
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        # Create the graph
        workflow = StateGraph(CharacterState)
        
        # Add nodes for each processing stage
        workflow.add_node("initialize", self._initialize_character)
        workflow.add_node("generate_stats", self._generate_stats)
        workflow.add_node("select_race", self._select_race)
        workflow.add_node("select_class", self._select_class)
        workflow.add_node("create_background", self._create_background)
        workflow.add_node("select_equipment", self._select_equipment)
        workflow.add_node("validate", self._validate_character)
        workflow.add_node("optimize", self._optimize_character)
        workflow.add_node("finalize", self._finalize_character)
        workflow.add_node("handle_error", self._handle_error)
        
        # Set entry point
        workflow.set_entry_point("initialize")
        
        # Add edges with conditional routing
        workflow.add_edge("initialize", "generate_stats")
        workflow.add_edge("generate_stats", "select_race")
        workflow.add_edge("select_race", "select_class")
        workflow.add_edge("select_class", "create_background")
        workflow.add_edge("create_background", "select_equipment")
        workflow.add_edge("select_equipment", "validate")
        
        # Conditional edges from validation
        workflow.add_conditional_edges(
            "validate",
            self._route_after_validation,
            {
                "optimize": "optimize",
                "complete": "finalize",
                "retry": "generate_stats",
                "error": "handle_error"
            }
        )
        
        workflow.add_edge("optimize", "finalize")
        workflow.add_edge("finalize", END)
        workflow.add_edge("handle_error", END)
        
        return workflow.compile()
    
    def _initialize_character(self, state: CharacterState) -> CharacterState:
        """Initialize character creation state."""
        logger.info("Initializing character creation")
        
        state["stage"] = ProcessingStage.INITIAL
        state["character_data"] = {
            "name": state.get("user_preferences", {}).get("name", "Unnamed Hero"),
            "system": state.get("system", GameSystem.DND5E),
        }
        state["errors"] = []
        state["warnings"] = []
        state["processing_history"] = ["Character creation initialized"]
        state["retry_count"] = 0
        state["is_complete"] = False
        
        return state
    
    def _generate_stats(self, state: CharacterState) -> CharacterState:
        """Generate ability scores."""
        logger.info("Generating ability scores")
        
        state["stage"] = ProcessingStage.STATS_GENERATION
        
        # Use stats agent to generate scores
        generation_method = state["user_preferences"].get("generation_method", "standard_array")
        stats = self.stats_agent.generate_ability_scores(
            method=generation_method,
            preferences=state["user_preferences"]
        )
        
        state["character_data"]["ability_scores"] = stats
        state["processing_history"].append(f"Generated ability scores using {generation_method}")
        
        return state
    
    def _select_race(self, state: CharacterState) -> CharacterState:
        """Select character race."""
        logger.info("Selecting character race")
        
        state["stage"] = ProcessingStage.RACE_SELECTION
        
        # For now, use preference or default
        race_name = state["user_preferences"].get("race", "Human")
        
        # TODO: Use race selection agent
        race_data = {
            "name": race_name,
            "ability_bonuses": self._get_racial_bonuses(race_name),
            "traits": self._get_racial_traits(race_name),
            "size": "Medium",
            "speed": 30,
            "languages": ["Common"]
        }
        
        state["character_data"]["race"] = race_data
        state["processing_history"].append(f"Selected race: {race_name}")
        
        return state
    
    def _select_class(self, state: CharacterState) -> CharacterState:
        """Select character class."""
        logger.info("Selecting character class")
        
        state["stage"] = ProcessingStage.CLASS_SELECTION
        
        # For now, use preference or default
        class_name = state["user_preferences"].get("class", "Fighter")
        level = state["user_preferences"].get("level", 1)
        
        # TODO: Use class selection agent
        class_data = {
            "name": class_name,
            "level": level,
            "hit_dice": self._get_hit_dice(class_name),
            "primary_ability": self._get_primary_ability(class_name),
            "saving_throws": self._get_saving_throws(class_name),
        }
        
        state["character_data"]["classes"] = [class_data]
        state["character_data"]["level"] = level
        state["processing_history"].append(f"Selected class: {class_name} (Level {level})")
        
        return state
    
    def _create_background(self, state: CharacterState) -> CharacterState:
        """Create character background."""
        logger.info("Creating character background")
        
        state["stage"] = ProcessingStage.BACKGROUND_CREATION
        
        # For now, use preference or default
        background_name = state["user_preferences"].get("background", "Folk Hero")
        
        # TODO: Use lore agent
        background_data = {
            "name": background_name,
            "skills": ["Animal Handling", "Survival"],
            "languages": [],
            "equipment": ["Artisan's tools", "Shovel", "Iron pot", "Common clothes"],
            "feature": "Rustic Hospitality"
        }
        
        state["character_data"]["background"] = background_data
        state["processing_history"].append(f"Created background: {background_name}")
        
        return state
    
    def _select_equipment(self, state: CharacterState) -> CharacterState:
        """Select character equipment."""
        logger.info("Selecting character equipment")
        
        state["stage"] = ProcessingStage.EQUIPMENT_SELECTION
        
        # TODO: Use equipment agent
        equipment_data = {
            "weapons": ["Longsword", "Shield"],
            "armor": "Chain mail",
            "shield": True,
            "tools": [],
            "other_items": ["Explorer's pack", "Rope (50 feet)"],
            "currency": {"gp": 10}
        }
        
        state["character_data"]["equipment"] = equipment_data
        state["processing_history"].append("Selected starting equipment")
        
        return state
    
    def _validate_character(self, state: CharacterState) -> CharacterState:
        """Validate the character."""
        logger.info("Validating character")
        
        state["stage"] = ProcessingStage.VALIDATION
        start_time = time.time()
        
        # Convert to Character model for validation
        try:
            # Add required fields for Character model
            character_data = state["character_data"].copy()
            character_data.update({
                "hit_points": 10,  # TODO: Calculate properly
                "max_hit_points": 10,
                "armor_class": 16,  # TODO: Calculate properly
                "proficiency_bonus": 2,  # TODO: Calculate based on level
            })
            
            character = Character.from_dict(character_data)
            
            # Run validation
            validation_result = self.validation_agent.validate(
                character=character,
                system=state["system"],
                strict_mode=True
            )
            
            validation_result.validation_time = time.time() - start_time
            state["validation_results"] = validation_result
            
            if validation_result.is_valid:
                state["processing_history"].append("Character validation passed")
            else:
                state["processing_history"].append(
                    f"Character validation failed with {len(validation_result.errors)} errors"
                )
                
        except Exception as e:
            logger.error(f"Validation error: {e}")
            state["errors"].append(str(e))
            state["processing_history"].append(f"Validation error: {e}")
            
        return state
    
    def _optimize_character(self, state: CharacterState) -> CharacterState:
        """Optimize the character build."""
        logger.info("Optimizing character")
        
        state["stage"] = ProcessingStage.OPTIMIZATION
        
        # TODO: Implement optimization agent
        state["processing_history"].append("Character optimization completed")
        
        return state
    
    def _finalize_character(self, state: CharacterState) -> CharacterState:
        """Finalize character creation."""
        logger.info("Finalizing character")
        
        state["stage"] = ProcessingStage.COMPLETE
        state["is_complete"] = True
        state["processing_history"].append("Character creation completed successfully")
        
        return state
    
    def _handle_error(self, state: CharacterState) -> CharacterState:
        """Handle errors in the workflow."""
        logger.error(f"Error in character creation: {state['errors']}")
        
        state["stage"] = ProcessingStage.ERROR
        state["is_complete"] = True
        state["processing_history"].append("Character creation failed due to errors")
        
        return state
    
    def _route_after_validation(self, state: CharacterState) -> str:
        """Route after validation based on results."""
        if state.get("errors"):
            return "error"
            
        validation_results = state.get("validation_results")
        if not validation_results:
            return "error"
            
        if not validation_results.is_valid:
            if state["retry_count"] < 3:
                state["retry_count"] += 1
                return "retry"
            else:
                return "error"
                
        if state["should_optimize"] and state["optimization_goals"]:
            return "optimize"
            
        return "complete"
    
    # Helper methods for getting game data
    # TODO: These should come from MCP servers or rule database
    
    def _get_racial_bonuses(self, race: str) -> Dict[str, int]:
        """Get racial ability bonuses."""
        bonuses = {
            "Human": {"strength": 1, "dexterity": 1, "constitution": 1, 
                     "intelligence": 1, "wisdom": 1, "charisma": 1},
            "Elf": {"dexterity": 2},
            "Dwarf": {"constitution": 2},
            "Halfling": {"dexterity": 2},
        }
        return bonuses.get(race, {})
    
    def _get_racial_traits(self, race: str) -> List[str]:
        """Get racial traits."""
        traits = {
            "Human": ["Versatile"],
            "Elf": ["Darkvision", "Keen Senses", "Fey Ancestry", "Trance"],
            "Dwarf": ["Darkvision", "Dwarven Resilience", "Stonecunning"],
            "Halfling": ["Lucky", "Brave", "Halfling Nimbleness"],
        }
        return traits.get(race, [])
    
    def _get_hit_dice(self, class_name: str) -> str:
        """Get hit dice for class."""
        hit_dice = {
            "Fighter": "d10",
            "Wizard": "d6",
            "Cleric": "d8",
            "Rogue": "d8",
        }
        return hit_dice.get(class_name, "d8")
    
    def _get_primary_ability(self, class_name: str) -> str:
        """Get primary ability for class."""
        abilities = {
            "Fighter": "strength",
            "Wizard": "intelligence",
            "Cleric": "wisdom",
            "Rogue": "dexterity",
        }
        return abilities.get(class_name, "strength")
    
    def _get_saving_throws(self, class_name: str) -> List[str]:
        """Get saving throw proficiencies for class."""
        saves = {
            "Fighter": ["strength", "constitution"],
            "Wizard": ["intelligence", "wisdom"],
            "Cleric": ["wisdom", "charisma"],
            "Rogue": ["dexterity", "intelligence"],
        }
        return saves.get(class_name, [])
    
    async def create_character(
        self,
        user_preferences: Dict[str, Any],
        system: GameSystem = GameSystem.DND5E,
        optimization_goals: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a character based on user preferences."""
        initial_state = {
            "user_preferences": user_preferences,
            "system": system,
            "optimization_goals": optimization_goals or [],
            "should_optimize": bool(optimization_goals),
        }
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state)
        
        return {
            "character": final_state.get("character_data"),
            "validation_results": final_state.get("validation_results"),
            "processing_history": final_state.get("processing_history"),
            "is_complete": final_state.get("is_complete"),
            "errors": final_state.get("errors"),
        } 