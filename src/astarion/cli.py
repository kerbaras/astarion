"""Main CLI interface for Astarion."""

import json
import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from loguru import logger

from astarion.core import get_settings, CharacterValidator
from astarion.core.orchestrator import CharacterCreationOrchestrator
from astarion.models.character import GameSystem
from astarion.rag.processor import RulebookProcessor

console = Console()

@click.group()
@click.version_option(version="0.1.0", prog_name="astarion")
def cli():
    """Astarion - Intelligent LLM-powered assistant for tabletop RPG character creation.
    
    Validate characters, process rulebooks, and optimize builds with AI assistance.
    """
    # Configure logging
    settings = get_settings()
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)


@cli.command()
@click.argument("character_file", type=click.Path(exists=True))
@click.option("--system", "-s", default="dnd5e", help="Game system (dnd5e, pathfinder)")
@click.option("--strict/--no-strict", default=True, help="Use strict validation mode")
@click.option("--output", "-o", type=click.Choice(["text", "json"]), default="text", help="Output format")
def validate(character_file: str, system: str, strict: bool, output: str):
    """Validate a character file against game rules.
    
    CHARACTER_FILE: Path to JSON file containing character data
    """
    console.print(f"[cyan]Validating character from {character_file}...[/cyan]")
    
    try:
        # Load character data
        with open(character_file, "r") as f:
            character_data = json.load(f)
            
        # Create validator
        validator = CharacterValidator(system=system)
        
        # Validate character
        result = validator.validate_character_sync(character_data, strict_mode=strict)
        
        if output == "json":
            # JSON output
            print(json.dumps(result.model_dump(), indent=2))
        else:
            # Rich text output
            _display_validation_result(result)
            
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--interactive/--no-interactive", "-i", default=True, help="Interactive mode")
@click.option("--system", "-s", default="dnd5e", help="Game system")
@click.option("--name", help="Character name")
@click.option("--race", help="Character race")
@click.option("--class", "char_class", help="Character class")
@click.option("--level", type=int, default=1, help="Character level")
@click.option("--method", type=click.Choice(["standard_array", "point_buy", "rolling"]), 
              default="standard_array", help="Ability score generation method")
@click.option("--optimize", is_flag=True, help="Enable optimization suggestions")
@click.option("--output", "-o", help="Output file path")
def create_character(
    interactive: bool, system: str, name: Optional[str], 
    race: Optional[str], char_class: Optional[str], level: int,
    method: str, optimize: bool, output: Optional[str]
):
    """Create a new character with intelligent assistance."""
    console.print("[cyan]Welcome to Astarion Character Creator![/cyan]")
    
    # Gather preferences
    preferences = {}
    
    if interactive:
        # Interactive mode
        if not name:
            name = click.prompt("Character name", default="Hero")
        if not race:
            race = click.prompt("Race", default="Human")
        if not char_class:
            char_class = click.prompt("Class", default="Fighter")
            
        preferences = {
            "name": name,
            "race": race,
            "class": char_class,
            "level": level,
            "generation_method": method
        }
        
        # Ask about optimization goals
        if optimize:
            console.print("\n[yellow]Optimization Goals:[/yellow]")
            console.print("1. Damage output")
            console.print("2. Survivability") 
            console.print("3. Skill versatility")
            console.print("4. Spellcasting power")
            goals = click.prompt("Select goals (comma-separated numbers)", default="1")
            
            goal_map = {
                "1": "damage",
                "2": "defense",
                "3": "skills",
                "4": "spellcasting"
            }
            preferences["optimization_goals"] = [
                goal_map.get(g.strip(), "damage") 
                for g in goals.split(",")
            ]
    else:
        # Non-interactive mode
        preferences = {
            "name": name or "Hero",
            "race": race or "Human",
            "class": char_class or "Fighter", 
            "level": level,
            "generation_method": method
        }
        
    # Create character
    console.print("\n[cyan]Creating character...[/cyan]")
    orchestrator = CharacterCreationOrchestrator()
    
    # Run synchronously for now
    import asyncio
    result = asyncio.run(orchestrator.create_character(
        user_preferences=preferences,
        system=GameSystem(system),
        optimization_goals=preferences.get("optimization_goals", [])
    ))
    
    if result["is_complete"] and not result.get("errors"):
        console.print("[green]Character created successfully![/green]")
        
        # Display character
        character = result["character"]
        _display_character(character)
        
        # Display validation results if available
        if result.get("validation_results"):
            _display_validation_result(result["validation_results"])
            
        # Save to file if requested
        if output:
            with open(output, "w") as f:
                json.dump(character, f, indent=2)
            console.print(f"\n[green]Character saved to {output}[/green]")
    else:
        console.print("[red]Character creation failed![/red]")
        for error in result.get("errors", []):
            console.print(f"  • {error}")


@cli.command()
@click.argument("pdf_file", type=click.Path(exists=True))
@click.option("--system", "-s", default="dnd5e", help="Game system")
@click.option("--book-name", "-b", help="Book name/abbreviation (e.g., PHB)")
@click.option("--version", "-v", help="Book version")
def add_rulebook(pdf_file: str, system: str, book_name: Optional[str], version: Optional[str]):
    """Process and add a rulebook PDF to the system.
    
    PDF_FILE: Path to the rulebook PDF file
    """
    console.print(f"[cyan]Processing rulebook: {pdf_file}[/cyan]")
    
    try:
        # Create processor
        processor = RulebookProcessor()
        
        # Process the PDF
        import asyncio
        asyncio.run(processor.process_pdf(
            pdf_path=pdf_file,
            system=system,
            book_name=book_name,
            version=version
        ))
        
        console.print("[green]Rulebook processed successfully![/green]")
        
    except Exception as e:
        console.print(f"[red]Error processing rulebook: {e}[/red]")
        sys.exit(1)


def _display_validation_result(result):
    """Display validation results in a nice format."""
    # Create status panel
    status_color = "green" if result.is_valid else "red"
    status_text = "VALID" if result.is_valid else "INVALID"
    
    panel = Panel(
        f"[{status_color}]{status_text}[/{status_color}]",
        title=f"Validation Result for {result.character_name}",
        subtitle=f"{result.game_system} | {result.rules_checked} rules checked"
    )
    console.print(panel)
    
    # Display errors
    if result.errors:
        console.print("\n[red]Errors:[/red]")
        for error in result.errors:
            console.print(f"  • {error.message}")
            if error.source:
                console.print(f"    [dim]Source: {error.source}[/dim]")
            if error.fix_suggestion:
                console.print(f"    [yellow]Fix: {error.fix_suggestion}[/yellow]")
                
    # Display warnings
    if result.warnings:
        console.print("\n[yellow]Warnings:[/yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning.message}")
            if warning.source:
                console.print(f"    [dim]Source: {warning.source}[/dim]")
                
    # Display optimization suggestions
    if result.optimization_suggestions:
        console.print("\n[cyan]Optimization Suggestions:[/cyan]")
        for opt in result.optimization_suggestions:
            console.print(f"  • [{opt.category}] {opt.reasoning}")
            console.print(f"    Current: {opt.current_value} → Suggested: {opt.suggested_value}")
            console.print(f"    [dim]Impact: {opt.impact}[/dim]")


def _display_character(character_data: dict):
    """Display character details in a nice format."""
    # Basic info
    console.print(f"\n[bold]{character_data['name']}[/bold]")
    console.print(f"Level {character_data['level']} {character_data['race']['name']} {character_data['classes'][0]['name']}")
    
    # Ability scores
    console.print("\n[cyan]Ability Scores:[/cyan]")
    scores = character_data["ability_scores"]
    table = Table(show_header=False)
    table.add_row("STR", str(scores["strength"]), "INT", str(scores["intelligence"]))
    table.add_row("DEX", str(scores["dexterity"]), "WIS", str(scores["wisdom"]))
    table.add_row("CON", str(scores["constitution"]), "CHA", str(scores["charisma"]))
    console.print(table)
    
    # Equipment
    if character_data.get("equipment"):
        console.print("\n[cyan]Equipment:[/cyan]")
        equipment = character_data["equipment"]
        if equipment.get("armor"):
            console.print(f"  Armor: {equipment['armor']}")
        if equipment.get("weapons"):
            console.print(f"  Weapons: {', '.join(equipment['weapons'])}")


if __name__ == "__main__":
    cli()


# For use as script entry point
app = cli 