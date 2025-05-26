"""Rule models for representing game rules."""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Types of rules in the system."""
    PREREQUISITE = "prerequisite"      # Requirements that must be met
    RESTRICTION = "restriction"        # Things that cannot be done
    PROGRESSION = "progression"        # Level-based features
    INTERACTION = "interaction"        # How rules affect each other
    CALCULATION = "calculation"        # Formulas and computations
    OPTION = "option"                 # Choices available to players
    

class RuleCondition(BaseModel):
    """Condition that must be met for a rule."""
    field: str = Field(description="Character field to check")
    operator: str = Field(description="Comparison operator (==, !=, >, <, >=, <=, in, not_in)")
    value: Any = Field(description="Value to compare against")
    
    def evaluate(self, character_data: Dict[str, Any]) -> bool:
        """Evaluate if condition is met."""
        # This is a simplified implementation
        field_value = character_data.get(self.field)
        
        if self.operator == "==":
            return field_value == self.value
        elif self.operator == "!=":
            return field_value != self.value
        elif self.operator == ">":
            return field_value > self.value
        elif self.operator == "<":
            return field_value < self.value
        elif self.operator == ">=":
            return field_value >= self.value
        elif self.operator == "<=":
            return field_value <= self.value
        elif self.operator == "in":
            return field_value in self.value
        elif self.operator == "not_in":
            return field_value not in self.value
        else:
            raise ValueError(f"Unknown operator: {self.operator}")


class RuleEffect(BaseModel):
    """Effect that a rule has when applied."""
    field: str = Field(description="Character field affected")
    action: str = Field(description="Action to take (set, add, remove, modify)")
    value: Any = Field(description="Value to apply")
    description: str = Field(description="Human-readable description")


class Rule(BaseModel):
    """Complete rule representation."""
    id: str = Field(description="Unique rule identifier")
    name: str = Field(description="Rule name")
    type: RuleType = Field(description="Type of rule")
    system: str = Field(description="Game system (e.g., 'dnd5e')")
    
    # Rule content
    description: str = Field(description="Full rule description")
    conditions: List[RuleCondition] = Field(default_factory=list, description="Conditions for rule to apply")
    effects: List[RuleEffect] = Field(default_factory=list, description="Effects when rule applies")
    
    # Source information
    source_book: str = Field(description="Source book abbreviation")
    source_page: int = Field(description="Page number")
    source_section: Optional[str] = Field(None, description="Section name")
    exact_text: Optional[str] = Field(None, description="Exact quote from source")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    related_rules: List[str] = Field(default_factory=list, description="Related rule IDs")
    overrides: List[str] = Field(default_factory=list, description="Rule IDs this overrides")
    overridden_by: List[str] = Field(default_factory=list, description="Rule IDs that override this")
    
    # Validation metadata
    priority: int = Field(100, description="Rule priority (lower = higher priority)")
    is_optional: bool = Field(False, description="Whether this is an optional rule")
    requires_dm_approval: bool = Field(False, description="Whether DM approval is needed")
    
    def applies_to(self, character_data: Dict[str, Any]) -> bool:
        """Check if rule applies to given character data."""
        if not self.conditions:
            return True
        return all(condition.evaluate(character_data) for condition in self.conditions)
    
    def get_source_citation(self) -> str:
        """Get formatted source citation."""
        citation = f"{self.source_book} p.{self.source_page}"
        if self.source_section:
            citation += f" ({self.source_section})"
        return citation


class RuleSet(BaseModel):
    """Collection of rules for a game system."""
    system: str = Field(description="Game system identifier")
    version: str = Field(description="Rules version")
    rules: List[Rule] = Field(default_factory=list, description="All rules in the set")
    
    # Indexes for fast lookup (using private attributes properly)
    model_config = {"arbitrary_types_allowed": True}
    
    def __init__(self, **data):
        """Initialize and build indexes."""
        super().__init__(**data)
        # Initialize indexes as instance attributes
        self._by_id: Dict[str, Rule] = {}
        self._by_type: Dict[RuleType, List[Rule]] = {}
        self._by_tag: Dict[str, List[Rule]] = {}
        self._rebuild_indexes()
        
    def _rebuild_indexes(self) -> None:
        """Rebuild internal indexes."""
        self._by_id.clear()
        self._by_type.clear()
        self._by_tag.clear()
        
        for rule in self.rules:
            # ID index
            self._by_id[rule.id] = rule
            
            # Type index
            if rule.type not in self._by_type:
                self._by_type[rule.type] = []
            self._by_type[rule.type].append(rule)
            
            # Tag index
            for tag in rule.tags:
                if tag not in self._by_tag:
                    self._by_tag[tag] = []
                self._by_tag[tag].append(rule)
                
    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the set."""
        self.rules.append(rule)
        self._rebuild_indexes()
        
    def get_rule(self, rule_id: str) -> Optional[Rule]:
        """Get rule by ID."""
        return self._by_id.get(rule_id)
        
    def get_rules_by_type(self, rule_type: RuleType) -> List[Rule]:
        """Get all rules of a specific type."""
        return self._by_type.get(rule_type, [])
        
    def get_rules_by_tag(self, tag: str) -> List[Rule]:
        """Get all rules with a specific tag."""
        return self._by_tag.get(tag, [])
        
    def get_applicable_rules(self, character_data: Dict[str, Any]) -> List[Rule]:
        """Get all rules that apply to the given character."""
        applicable = []
        for rule in self.rules:
            if rule.applies_to(character_data):
                applicable.append(rule)
                
        # Sort by priority
        applicable.sort(key=lambda r: r.priority)
        return applicable
        
    def validate_character(self, character_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate character against all rules."""
        violations = []
        applicable_rules = self.get_applicable_rules(character_data)
        
        for rule in applicable_rules:
            # This is a simplified validation
            # In practice, each rule type would have specific validation logic
            if rule.type == RuleType.RESTRICTION:
                # Check if restriction is violated
                for effect in rule.effects:
                    current_value = character_data.get(effect.field)
                    if effect.action == "not_allowed" and current_value == effect.value:
                        violations.append({
                            "rule_id": rule.id,
                            "rule_name": rule.name,
                            "message": f"{effect.description}",
                            "source": rule.get_source_citation()
                        })
                        
        return violations 