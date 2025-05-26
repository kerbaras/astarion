# Contributing to Astarion

First off, thank you for considering contributing to Astarion! 🎲 It's people like you that make Astarion such a great tool for the tabletop RPG community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Style Guidelines](#style-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)
- [Documentation](#documentation)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [conduct@astarion.ai](mailto:conduct@astarion.ai).

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of:
- Experience level (from first-time contributors to veteran developers)
- RPG system preference (D&D, Pathfinder, or any other system!)
- Background, identity, or personal characteristics

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.10 or higher
- Git
- A GitHub account
- Basic familiarity with Git and GitHub workflow
- (Optional) Experience with tabletop RPGs is helpful but not required!

### First Contributions

Not sure where to start? Look for issues labeled:
- `good first issue` - Simple tasks perfect for newcomers
- `help wanted` - Tasks where we need community assistance
- `documentation` - Help improve our docs (no coding required!)
- `rulebook-data` - Help verify RPG rule implementations

## How Can I Contribute?

### 🐛 Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

```markdown
**Description**
A clear and concise description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Initialize character with '...'
2. Add class '...'
3. Apply feat '...'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened, including any error messages.

**System Information**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Astarion version: [e.g., 0.1.0]
- RPG System: [e.g., D&D 5e]

**Additional Context**
Add any other context, including rulebook references if applicable.
```

### 💡 Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- **Use case**: Explain the problem you're trying to solve
- **Proposed solution**: Describe how you envision it working
- **Alternatives considered**: List any alternative solutions you've thought about
- **RPG context**: If relevant, explain which game systems would benefit

### 📚 Adding Rulebook Support

Want to add support for a new RPG system? Here's how:

1. **Create an issue** discussing the system you want to add
2. **Gather resources**: Ensure you have legal access to the rulebooks
3. **Start with core rules**: Focus on character creation basics first
4. **Follow the pattern**: Look at existing implementations (D&D 5e, Pathfinder)
5. **Add tests**: Every rule needs test cases

### 🎨 Improving the UI/UX

- Mockups and design suggestions are welcome!
- Consider accessibility in all designs
- Test with actual RPG players when possible

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/astarion.git
cd astarion
git remote add upstream https://github.com/originalowner/astarion.git
```

### 2. Create Virtual Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### 3. Set Up Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually (optional)
pre-commit run --all-files
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
# For development, minimal configuration is usually fine
```

### 5. Run Development Server

```bash
# Start the development server
python -m astarion.main --dev

# Or use the development script
./scripts/dev.sh  # On Windows: scripts\dev.bat
```

## Style Guidelines

### Python Code Style

We use [Black](https://black.readthedocs.io/) for code formatting and follow [PEP 8](https://pep8.org/):

```python
# Good example
class CharacterValidator:
    """Validates character data against rulebook constraints."""
    
    def __init__(self, ruleset: str = "dnd5e"):
        self.ruleset = ruleset
        self.rules = self._load_rules()
    
    def validate_ability_scores(
        self, 
        scores: dict[str, int]
    ) -> ValidationResult:
        """Validate ability scores against ruleset constraints.
        
        Args:
            scores: Dictionary mapping ability names to values
            
        Returns:
            ValidationResult with any errors or warnings
        """
        # Implementation here
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import Optional, Union

def calculate_modifier(
    score: int, 
    bonus: Optional[int] = None
) -> int:
    """Calculate ability modifier from score."""
    base_modifier = (score - 10) // 2
    return base_modifier + (bonus or 0)
```

### Docstrings

Use Google-style docstrings:

```python
def add_class_level(
    character: Character,
    class_name: str,
    subclass: Optional[str] = None
) -> Character:
    """Add a class level to a character.
    
    Args:
        character: The character to modify
        class_name: Name of the class to add
        subclass: Optional subclass choice
        
    Returns:
        Updated character with new class level
        
    Raises:
        ValidationError: If prerequisites not met
        
    Example:
        >>> char = Character(name="Elara")
        >>> char = add_class_level(char, "wizard")
    """
```

### File Organization

```
astarion/
├── agents/           # One file per agent type
├── mcp/
│   └── {system}/    # One directory per game system
├── rules/
│   └── {system}/    # Rules organized by system
├── rag/
│   ├── extractors/  # PDF extraction logic
│   ├── chunkers/    # Document chunking strategies
│   └── embedders/   # Embedding generation
└── tests/          # Mirror the source structure
```

## Commit Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples

```bash
# Feature
feat(rules): add D&D 5e multiclassing validation

# Bug fix
fix(character): correct ability modifier calculation

# Documentation
docs(api): update character creation examples

# With scope and body
feat(mcp): add Pathfinder 2e spell validation

Implements MCP server endpoints for:
- Spell prerequisite checking
- Spell slot calculation
- Prepared spell validation

Closes #123
```

## Pull Request Process

### 1. Create a Feature Branch

```bash
# Update your fork
git checkout main
git pull upstream main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Write code following our style guidelines
- Add/update tests as needed
- Update documentation
- Run tests locally

### 3. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with conventional commit message
git commit -m "feat(component): add amazing feature"
```

### 4. Push to Your Fork

```bash
git push origin feature/your-feature-name
```

### 5. Create Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No new warnings
```

### 6. Code Review

- Respond to feedback constructively
- Make requested changes
- Push additional commits to your branch
- Mark conversations as resolved

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/rules/test_dnd5e.py

# Run with coverage
pytest --cov=astarion --cov-report=html

# Run only fast tests
pytest -m "not slow"
```

### Writing Tests

```python
# Good test example
def test_multiclass_prerequisites():
    """Test that multiclass prerequisites are enforced."""
    # Arrange
    character = Character(
        name="Test Character",
        abilities={"STR": 13, "DEX": 10, "CON": 12, 
                  "INT": 8, "WIS": 13, "CHA": 14}
    )
    
    # Act & Assert - Valid multiclass
    result = validate_multiclass(character, "fighter", "cleric")
    assert result.is_valid
    
    # Act & Assert - Invalid multiclass
    result = validate_multiclass(character, "wizard", "sorcerer")
    assert not result.is_valid
    assert "Intelligence 13 required" in result.errors[0]
```

### Test Categories

- **Unit Tests**: Test individual functions/methods
- **Integration Tests**: Test component interactions
- **Rule Tests**: Validate RPG rule implementations
- **E2E Tests**: Test complete workflows

## Documentation

### Code Documentation

- Every public function needs a docstring
- Complex algorithms need inline comments
- Update README.md for significant features

### RPG Rule Documentation

When implementing game rules:

```python
def calculate_spell_save_dc(character: Character) -> int:
    """Calculate spell save DC for character.
    
    Per PHB p.205: Spell save DC = 8 + proficiency bonus + 
    spellcasting ability modifier
    
    Args:
        character: Character with spellcasting ability
        
    Returns:
        Spell save DC value
    """
    # Implementation with source comments
```

### API Documentation

- Use OpenAPI/Swagger annotations
- Include request/response examples
- Document error codes and meanings

## Community

### Discord

Join our [Discord server](https://discord.gg/astarion) for:
- Real-time help with contributions
- Design discussions
- Community playtesting
- General RPG chat

### Forums

- Use GitHub Discussions for long-form conversations
- Stack Overflow tag: `astarion-rpg`

### Communication Guidelines

- Be respectful and inclusive
- No gatekeeping about RPG knowledge
- Assume positive intent
- Help newcomers get started

## Recognition

Contributors are recognized in several ways:
- Listed in [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Mentioned in release notes
- Special Discord roles
- Eternal gratitude from the RPG community! 🎲

## Questions?

If you have questions not covered here:
1. Check our [FAQ](docs/FAQ.md)
2. Ask in Discord
3. Open a discussion on GitHub
4. Email [contributors@astarion.ai](mailto:contributors@astarion.ai)

---

Thank you again for contributing to Astarion! May your pull requests always pass their saving throws! 🎲✨
