"""Validation models for character validation results."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for validation issues."""
    ERROR = "error"       # Character is invalid
    WARNING = "warning"   # Character is valid but suboptimal
    INFO = "info"        # Informational message
    

class RuleSource(BaseModel):
    """Source citation for a rule."""
    book: str = Field(description="Book abbreviation (e.g., 'PHB', 'DMG')")
    page: int = Field(description="Page number")
    section: Optional[str] = Field(None, description="Section or chapter name")
    quote: Optional[str] = Field(None, description="Exact quote from the source")
    
    def __str__(self) -> str:
        """Format source as citation."""
        base = f"{self.book} p.{self.page}"
        if self.section:
            base = f"{base} ({self.section})"
        if self.quote:
            base = f'{base} "{self.quote}"'
        return base


class ValidationIssue(BaseModel):
    """Base class for validation issues."""
    severity: Severity = Field(description="Issue severity")
    rule_id: str = Field(description="Unique rule identifier")
    message: str = Field(description="Human-readable message")
    field: Optional[str] = Field(None, description="Character field affected")
    source: Optional[RuleSource] = Field(None, description="Rule source citation")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")


class ValidationError(ValidationIssue):
    """Validation error - character is invalid."""
    severity: Severity = Field(Severity.ERROR, frozen=True)
    fix_suggestion: Optional[str] = Field(None, description="How to fix the error")


class ValidationWarning(ValidationIssue):
    """Validation warning - character is valid but has issues."""
    severity: Severity = Field(Severity.WARNING, frozen=True)
    optimization_suggestion: Optional[str] = Field(None, description="Optimization tip")


class ValidationInfo(ValidationIssue):
    """Validation info - informational message."""
    severity: Severity = Field(Severity.INFO, frozen=True)


class OptimizationSuggestion(BaseModel):
    """Optimization suggestion for character build."""
    category: str = Field(description="Optimization category (e.g., 'damage', 'defense')")
    current_value: Any = Field(description="Current value or choice")
    suggested_value: Any = Field(description="Suggested value or choice")
    impact: str = Field(description="Expected impact of the change")
    reasoning: str = Field(description="Why this change is beneficial")
    sources: List[RuleSource] = Field(default_factory=list, description="Supporting sources")
    priority: int = Field(ge=1, le=5, description="Priority (1=highest, 5=lowest)")


class ValidationResult(BaseModel):
    """Complete validation result for a character."""
    is_valid: bool = Field(description="Whether the character is valid")
    errors: List[ValidationError] = Field(default_factory=list)
    warnings: List[ValidationWarning] = Field(default_factory=list)
    info: List[ValidationInfo] = Field(default_factory=list)
    optimization_suggestions: List[OptimizationSuggestion] = Field(default_factory=list)
    
    # Metadata
    character_name: str = Field(description="Character being validated")
    game_system: str = Field(description="Game system used")
    validation_time: float = Field(description="Time taken to validate (seconds)")
    rules_checked: int = Field(description="Number of rules checked")
    
    # Summary statistics
    total_issues: int = Field(0, description="Total number of issues found")
    
    def __init__(self, **data):
        """Initialize and calculate derived fields."""
        super().__init__(**data)
        self.total_issues = len(self.errors) + len(self.warnings)
        
    def add_error(self, error: ValidationError) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
        self.total_issues += 1
        
    def add_warning(self, warning: ValidationWarning) -> None:
        """Add a validation warning."""
        self.warnings.append(warning)
        self.total_issues += 1
        
    def add_info(self, info: ValidationInfo) -> None:
        """Add an informational message."""
        self.info.append(info)
        
    def add_optimization(self, suggestion: OptimizationSuggestion) -> None:
        """Add an optimization suggestion."""
        self.optimization_suggestions.append(suggestion)
        # Sort by priority
        self.optimization_suggestions.sort(key=lambda x: x.priority)
        
    def get_issues_by_field(self, field: str) -> List[ValidationIssue]:
        """Get all issues for a specific field."""
        all_issues = self.errors + self.warnings + self.info
        return [issue for issue in all_issues if issue.field == field]
    
    def get_issues_by_severity(self, severity: Severity) -> List[ValidationIssue]:
        """Get all issues of a specific severity."""
        if severity == Severity.ERROR:
            return self.errors
        elif severity == Severity.WARNING:
            return self.warnings
        else:
            return self.info
            
    def to_report(self) -> str:
        """Generate a human-readable validation report."""
        lines = [
            f"Validation Report for {self.character_name} ({self.game_system})",
            "=" * 60,
            f"Status: {'VALID' if self.is_valid else 'INVALID'}",
            f"Rules Checked: {self.rules_checked}",
            f"Validation Time: {self.validation_time:.2f}s",
            ""
        ]
        
        if self.errors:
            lines.append(f"ERRORS ({len(self.errors)}):")
            lines.append("-" * 40)
            for error in self.errors:
                lines.append(f"• {error.message}")
                if error.source:
                    lines.append(f"  Source: {error.source}")
                if error.fix_suggestion:
                    lines.append(f"  Fix: {error.fix_suggestion}")
                lines.append("")
                
        if self.warnings:
            lines.append(f"WARNINGS ({len(self.warnings)}):")
            lines.append("-" * 40)
            for warning in self.warnings:
                lines.append(f"• {warning.message}")
                if warning.source:
                    lines.append(f"  Source: {warning.source}")
                if warning.optimization_suggestion:
                    lines.append(f"  Tip: {warning.optimization_suggestion}")
                lines.append("")
                
        if self.optimization_suggestions:
            lines.append(f"OPTIMIZATION SUGGESTIONS ({len(self.optimization_suggestions)}):")
            lines.append("-" * 40)
            for opt in self.optimization_suggestions:
                lines.append(f"• [{opt.category}] {opt.reasoning}")
                lines.append(f"  Current: {opt.current_value} → Suggested: {opt.suggested_value}")
                lines.append(f"  Impact: {opt.impact}")
                lines.append("")
                
        return "\n".join(lines) 