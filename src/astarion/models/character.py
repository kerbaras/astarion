"""Character models for RPG character representation."""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class GameSystem(str, Enum):
    """Supported game systems."""
    DND5E = "dnd5e"
    PATHFINDER = "pathfinder"
    

class AbilityScores(BaseModel):
    """Character ability scores."""
    strength: int = Field(ge=1, le=30, description="Strength score")
    dexterity: int = Field(ge=1, le=30, description="Dexterity score")
    constitution: int = Field(ge=1, le=30, description="Constitution score")
    intelligence: int = Field(ge=1, le=30, description="Intelligence score")
    wisdom: int = Field(ge=1, le=30, description="Wisdom score")
    charisma: int = Field(ge=1, le=30, description="Charisma score")
    
    @field_validator("*", mode="before")
    def validate_ability_range(cls, v: Any) -> int:
        """Ensure ability scores are within valid range."""
        if isinstance(v, int) and not (1 <= v <= 30):
            raise ValueError(f"Ability score must be between 1 and 30, got {v}")
        return v
    
    def get_modifier(self, ability: str) -> int:
        """Calculate ability modifier."""
        score = getattr(self, ability.lower())
        return (score - 10) // 2


class Race(BaseModel):
    """Character race information."""
    name: str = Field(description="Race name (e.g., 'Human', 'Elf')")
    subrace: Optional[str] = Field(None, description="Subrace if applicable")
    traits: List[str] = Field(default_factory=list, description="Racial traits")
    ability_bonuses: Dict[str, int] = Field(
        default_factory=dict, 
        description="Ability score bonuses from race"
    )
    size: str = Field("Medium", description="Character size")
    speed: int = Field(30, description="Base walking speed in feet")
    languages: List[str] = Field(default_factory=list, description="Known languages")


class CharacterClass(BaseModel):
    """Character class information."""
    name: str = Field(description="Class name (e.g., 'Fighter', 'Wizard')")
    level: int = Field(ge=1, le=20, description="Class level")
    subclass: Optional[str] = Field(None, description="Subclass/archetype if chosen")
    hit_dice: str = Field(description="Hit dice (e.g., 'd10')")
    primary_ability: str = Field(description="Primary ability for the class")
    saving_throws: List[str] = Field(
        default_factory=list, 
        description="Proficient saving throws"
    )
    skills: List[str] = Field(default_factory=list, description="Class skills")
    features: List[str] = Field(default_factory=list, description="Class features")


class Background(BaseModel):
    """Character background information."""
    name: str = Field(description="Background name")
    skills: List[str] = Field(default_factory=list, description="Background skills")
    languages: List[str] = Field(default_factory=list, description="Background languages")
    equipment: List[str] = Field(default_factory=list, description="Starting equipment")
    feature: Optional[str] = Field(None, description="Background feature")
    personality_traits: List[str] = Field(default_factory=list, max_length=2)
    ideals: List[str] = Field(default_factory=list, max_length=1)
    bonds: List[str] = Field(default_factory=list, max_length=1)
    flaws: List[str] = Field(default_factory=list, max_length=1)


class Equipment(BaseModel):
    """Character equipment."""
    weapons: List[str] = Field(default_factory=list)
    armor: Optional[str] = Field(None)
    shield: bool = Field(False)
    tools: List[str] = Field(default_factory=list)
    other_items: List[str] = Field(default_factory=list)
    currency: Dict[str, int] = Field(
        default_factory=lambda: {"cp": 0, "sp": 0, "ep": 0, "gp": 0, "pp": 0}
    )


class Spell(BaseModel):
    """Spell representation."""
    name: str
    level: int = Field(ge=0, le=9)
    school: str
    casting_time: str
    range: str
    components: List[str]
    duration: str
    description: str
    source: str


class Character(BaseModel):
    """Complete character representation."""
    model_config = ConfigDict(use_enum_values=True)
    
    # Basic Information
    name: str = Field(description="Character name")
    system: GameSystem = Field(description="Game system")
    level: int = Field(ge=1, le=20, description="Total character level")
    experience_points: int = Field(ge=0, default=0)
    
    # Core Attributes
    race: Race = Field(description="Character race")
    classes: List[CharacterClass] = Field(description="Character classes (for multiclass)")
    background: Background = Field(description="Character background")
    alignment: Optional[str] = Field(None, description="Character alignment")
    
    # Abilities
    ability_scores: AbilityScores = Field(description="Base ability scores")
    
    # Combat Stats
    hit_points: int = Field(ge=0, description="Current hit points")
    max_hit_points: int = Field(ge=1, description="Maximum hit points")
    armor_class: int = Field(ge=0, description="Armor class")
    initiative_bonus: int = Field(default=0, description="Initiative modifier")
    proficiency_bonus: int = Field(ge=2, le=6, description="Proficiency bonus")
    
    # Proficiencies
    skill_proficiencies: List[str] = Field(default_factory=list)
    tool_proficiencies: List[str] = Field(default_factory=list)
    weapon_proficiencies: List[str] = Field(default_factory=list)
    armor_proficiencies: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    
    # Equipment
    equipment: Equipment = Field(default_factory=Equipment)
    
    # Spellcasting
    spellcasting_ability: Optional[str] = Field(None)
    spell_slots: Dict[int, int] = Field(default_factory=dict)
    spells_known: List[Spell] = Field(default_factory=list)
    spells_prepared: List[str] = Field(default_factory=list)
    
    # Features and Traits
    features: List[str] = Field(default_factory=list, description="All features and traits")
    feats: List[str] = Field(default_factory=list, description="Selected feats")
    
    # Metadata
    creation_method: str = Field("standard", description="How abilities were generated")
    optimization_goals: List[str] = Field(default_factory=list)
    notes: str = Field("", description="Additional notes")
    
    @field_validator("classes")
    def validate_multiclass_levels(cls, classes: List[CharacterClass], info) -> List[CharacterClass]:
        """Ensure total levels match character level."""
        if "level" in info.data:
            total_levels = sum(c.level for c in classes)
            if total_levels != info.data["level"]:
                raise ValueError(f"Total class levels ({total_levels}) must equal character level ({info.data['level']})")
        return classes
    
    def get_total_ability_score(self, ability: str) -> int:
        """Get total ability score including racial bonuses."""
        base = getattr(self.ability_scores, ability.lower())
        racial_bonus = self.race.ability_bonuses.get(ability.lower(), 0)
        # TODO: Add other bonuses (feats, magic items, etc.)
        return base + racial_bonus
    
    def get_ability_modifier(self, ability: str) -> int:
        """Get ability modifier including all bonuses."""
        total = self.get_total_ability_score(ability)
        return (total - 10) // 2
    
    def get_skill_modifier(self, skill: str, ability: str) -> int:
        """Calculate skill modifier."""
        ability_mod = self.get_ability_modifier(ability)
        if skill in self.skill_proficiencies:
            return ability_mod + self.proficiency_bonus
        return ability_mod
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert character to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Character":
        """Create character from dictionary."""
        return cls(**data) 