"""Astarion - Intelligent LLM-powered assistant for tabletop RPG character creation."""

__version__ = "0.1.0"
__author__ = "Astarion Team"

from astarion.core.validator import CharacterValidator
from astarion.rag.processor import RulebookProcessor

__all__ = ["CharacterValidator", "RulebookProcessor"] 