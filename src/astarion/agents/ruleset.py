"""Ruleset Agent for querying game rules from the RAG system."""

from typing import List, Dict, Any, Optional

from loguru import logger
from pydantic import BaseModel, Field

from .base import BaseAgent
from ..models.character import GameSystem
from ..models.validation import RuleSource
from ..rag.processor import RulebookProcessor
from ..rag.extractor import ContentType


class RuleQuery(BaseModel):
    """A query for game rules."""
    query: str = Field(description="The rule query")
    game_system: GameSystem = Field(description="Game system to query")
    content_types: Optional[List[ContentType]] = Field(
        None,
        description="Specific content types to search"
    )
    limit: int = Field(5, description="Maximum number of results")
    

class RuleResult(BaseModel):
    """A rule search result with citation."""
    text: str = Field(description="The rule text")
    citation: str = Field(description="Source citation")
    relevance_score: float = Field(description="Relevance score (0-1)")
    page_number: Optional[int] = Field(None, description="Page number")
    rule_type: Optional[str] = Field(None, description="Type of rule content")
    

class RulesetAgent(BaseAgent):
    """Agent that queries the RAG system for rule knowledge."""
    
    def __init__(self):
        """Initialize the Ruleset Agent."""
        super().__init__(
            name="RulesetAgent",
            description="Queries indexed rulebooks for game rules and mechanics"
        )
        self.processor = RulebookProcessor()
        
    async def query_rules(
        self,
        query: str,
        game_system: GameSystem = GameSystem.DND5E,
        content_types: Optional[List[ContentType]] = None,
        limit: int = 5
    ) -> List[RuleResult]:
        """Query the RAG system for relevant rules.
        
        Args:
            query: Natural language query
            game_system: Game system to search
            content_types: Specific content types to filter
            limit: Maximum results to return
            
        Returns:
            List of rule results with citations
        """
        logger.info(f"Querying rules: '{query}' in {game_system}")
        
        # Convert content types to strings if provided
        content_type_strings = None
        if content_types:
            content_type_strings = [ct.value for ct in content_types]
            
        # Search the RAG system
        search_results = await self.processor.search(
            query=query,
            system=game_system.value,
            limit=limit,
            content_types=content_type_strings
        )
        
        # Convert to RuleResult objects
        rule_results = []
        for result in search_results:
            rule_result = RuleResult(
                text=result["text"],
                citation=result.get("citation", "Unknown Source"),
                relevance_score=result.get("score", 0.0),
                page_number=result.get("metadata", {}).get("page_number"),
                rule_type=result.get("metadata", {}).get("chunk_type")
            )
            rule_results.append(rule_result)
            
        logger.info(f"Found {len(rule_results)} relevant rules")
        return rule_results
        
    async def find_spell(
        self,
        spell_name: str,
        game_system: GameSystem = GameSystem.DND5E
    ) -> Optional[RuleResult]:
        """Find a specific spell by name.
        
        Args:
            spell_name: Name of the spell
            game_system: Game system
            
        Returns:
            Spell details if found
        """
        results = await self.query_rules(
            query=f"spell {spell_name}",
            game_system=game_system,
            content_types=[ContentType.SPELL],
            limit=3
        )
        
        # Find best match
        for result in results:
            if spell_name.lower() in result.text.lower():
                return result
                
        return results[0] if results else None
        
    async def find_feat(
        self,
        feat_name: str,
        game_system: GameSystem = GameSystem.DND5E
    ) -> Optional[RuleResult]:
        """Find a specific feat by name.
        
        Args:
            feat_name: Name of the feat
            game_system: Game system
            
        Returns:
            Feat details if found
        """
        results = await self.query_rules(
            query=f"feat {feat_name}",
            game_system=game_system,
            content_types=[ContentType.FEAT],
            limit=3
        )
        
        # Find best match
        for result in results:
            if feat_name.lower() in result.text.lower():
                return result
                
        return results[0] if results else None
        
    async def check_prerequisite(
        self,
        feature_name: str,
        game_system: GameSystem = GameSystem.DND5E
    ) -> Optional[str]:
        """Check prerequisites for a feature.
        
        Args:
            feature_name: Name of the feature/feat/ability
            game_system: Game system
            
        Returns:
            Prerequisites text if found
        """
        results = await self.query_rules(
            query=f"{feature_name} prerequisite requirements",
            game_system=game_system,
            limit=3
        )
        
        for result in results:
            # Look for prerequisite mentions
            text_lower = result.text.lower()
            if "prerequisite" in text_lower and feature_name.lower() in text_lower:
                # Extract prerequisite text
                lines = result.text.split('\n')
                for i, line in enumerate(lines):
                    if "prerequisite" in line.lower():
                        # Return this line and potentially the next
                        prereq_text = line.strip()
                        if i + 1 < len(lines) and not lines[i + 1].strip().endswith(':'):
                            prereq_text += " " + lines[i + 1].strip()
                        return prereq_text
                        
        return None
        
    async def lookup_table(
        self,
        table_name: str,
        game_system: GameSystem = GameSystem.DND5E
    ) -> Optional[RuleResult]:
        """Look up a specific table.
        
        Args:
            table_name: Name or description of the table
            game_system: Game system
            
        Returns:
            Table data if found
        """
        results = await self.query_rules(
            query=f"table {table_name}",
            game_system=game_system,
            content_types=[ContentType.TABLE],
            limit=5
        )
        
        # Find best matching table
        for result in results:
            if table_name.lower() in result.text.lower():
                return result
                
        return results[0] if results else None
        
    async def get_class_features(
        self,
        class_name: str,
        level: Optional[int] = None,
        game_system: GameSystem = GameSystem.DND5E
    ) -> List[RuleResult]:
        """Get class features for a specific class and level.
        
        Args:
            class_name: Name of the class
            level: Specific level (optional)
            game_system: Game system
            
        Returns:
            List of class features
        """
        if level:
            query = f"{class_name} class features level {level}"
        else:
            query = f"{class_name} class features abilities"
            
        results = await self.query_rules(
            query=query,
            game_system=game_system,
            content_types=[ContentType.CLASS_FEATURE, ContentType.TEXT],
            limit=10
        )
        
        # Filter to most relevant
        if level:
            filtered = []
            for result in results:
                text_lower = result.text.lower()
                if (f"level {level}" in text_lower or 
                    f"{level}th level" in text_lower or
                    f"{level}st level" in text_lower or
                    f"{level}nd level" in text_lower or
                    f"{level}rd level" in text_lower):
                    filtered.append(result)
            return filtered
            
        return results
        
    async def validate_rule_interaction(
        self,
        rule1: str,
        rule2: str,
        game_system: GameSystem = GameSystem.DND5E
    ) -> Dict[str, Any]:
        """Check how two rules interact.
        
        Args:
            rule1: First rule/feature name
            rule2: Second rule/feature name
            game_system: Game system
            
        Returns:
            Analysis of rule interaction
        """
        # Search for both rules together
        combined_results = await self.query_rules(
            query=f"{rule1} {rule2} interaction combination",
            game_system=game_system,
            limit=5
        )
        
        # Search for each individually
        rule1_results = await self.query_rules(
            query=rule1,
            game_system=game_system,
            limit=2
        )
        
        rule2_results = await self.query_rules(
            query=rule2,
            game_system=game_system,
            limit=2
        )
        
        return {
            "rule1": rule1_results[0] if rule1_results else None,
            "rule2": rule2_results[0] if rule2_results else None,
            "interactions": combined_results,
            "conflicts": self._analyze_conflicts(rule1_results, rule2_results)
        }
        
    def _analyze_conflicts(
        self,
        rule1_results: List[RuleResult],
        rule2_results: List[RuleResult]
    ) -> List[str]:
        """Analyze potential conflicts between rules."""
        conflicts = []
        
        # Simple conflict detection
        if rule1_results and rule2_results:
            rule1_text = rule1_results[0].text.lower()
            rule2_text = rule2_results[0].text.lower()
            
            # Check for mutually exclusive keywords
            exclusive_pairs = [
                ("cannot", "must"),
                ("never", "always"),
                ("instead of", "in addition to"),
                ("replaces", "stacks with")
            ]
            
            for neg, pos in exclusive_pairs:
                if neg in rule1_text and pos in rule2_text:
                    conflicts.append(f"Potential conflict: {neg} vs {pos}")
                elif pos in rule1_text and neg in rule2_text:
                    conflicts.append(f"Potential conflict: {pos} vs {neg}")
                    
        return conflicts
        
    def create_rule_source(self, rule_result: RuleResult) -> RuleSource:
        """Convert a RuleResult to a RuleSource for validation."""
        return RuleSource(
            book=rule_result.citation.split(",")[0] if "," in rule_result.citation else rule_result.citation,
            page=rule_result.page_number,
            section=rule_result.rule_type,
            rule_text=rule_result.text[:200] + "..." if len(rule_result.text) > 200 else rule_result.text
        ) 