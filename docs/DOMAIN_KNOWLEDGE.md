# RPG DOMAIN KNOWLEDGE & RULE PROCESSING

## UNDERSTANDING RPG RULES

### Rule Hierarchy
RPG rules form a complex hierarchy of dependencies:

```
Core Rules (ability scores, basic mechanics)
    ↓
Race Rules (bonuses, restrictions, features)
    ↓
Class Rules (prerequisites, progressions, features)
    ↓
Feat Rules (prerequisites, effects, limitations)
    ↓
Equipment Rules (proficiencies, restrictions)
    ↓
Spell Rules (prerequisites, components, effects)
```

### Rule Types Astarion Handles

1. **Prerequisites**: Conditions that must be met (e.g., "Strength 13 to multiclass as Fighter")
2. **Restrictions**: Things that cannot be combined (e.g., "Druids will not wear metal armor")
3. **Progressions**: Features gained at specific levels
4. **Interactions**: How different rules affect each other
5. **Exceptions**: Special cases that override general rules
6. **Optional Rules**: Variant systems that may or may not apply

## CHARACTER CREATION WORKFLOW

### Standard Creation Process
1. **Choose Generation Method**: Point buy, standard array, or rolling
2. **Select Race**: Determines ability bonuses and racial features
3. **Generate Ability Scores**: Core statistics (STR, DEX, CON, INT, WIS, CHA)
4. **Select Class**: Determines hit points, proficiencies, and features
5. **Choose Background**: Provides skills and story hooks
6. **Select Starting Equipment**: Based on class and background
7. **Make Choices**: Spells, fighting styles, etc. based on class

### Validation Points
At each step, Astarion validates:
- **Legality**: Is this combination allowed?
- **Prerequisites**: Are requirements met?
- **Optimization**: Is this choice optimal for stated goals?
- **Completeness**: Are all required choices made?

## RULE COMPLEXITY EXAMPLES

### Simple Rule
"Elves have Darkvision to 60 feet"
- **Type**: Racial feature
- **Validation**: Automatic when race is Elf
- **Source**: Single location in rulebook

### Complex Rule
"Multiclassing requires meeting prerequisites for both current and new class"
- **Type**: Character progression
- **Validation**: Check ability scores against both class tables
- **Dependencies**: Ability scores, current class, target class
- **Exceptions**: Some DM discretion allowed

### Ambiguous Rule
"Sneak Attack works with finesse or ranged weapons"
- **Interpretation Needed**: What about thrown finesse weapons?
- **Astarion's Approach**: Cite official clarifications when available
- **Fallback**: Provide common interpretations with sources

## RULE EXTRACTION CHALLENGES

### PDF Structure Variations
Different publishers format rules differently:
- **Structured**: Clear headers, consistent formatting
- **Narrative**: Rules embedded in descriptive text
- **Tabular**: Key information in tables
- **Mixed**: Combination of all formats

### Extraction Strategies
1. **Pattern Recognition**: Identify common rule patterns
2. **Contextual Understanding**: Use surrounding text for clarity
3. **Table Parsing**: Extract structured data accurately
4. **Cross-Reference**: Connect related rules across pages

## GAME SYSTEM DIFFERENCES

### D&D 5th Edition
- **Advantage/Disadvantage**: Binary system, doesn't stack
- **Bounded Accuracy**: Numbers stay within reasonable ranges
- **Concentration**: Limits spell stacking
- **Action Economy**: Action, bonus action, reaction framework

### Pathfinder
- **Feat Trees**: Complex prerequisite chains
- **Skill Points**: Granular skill advancement
- **Combat Maneuvers**: Detailed tactical options
- **Archetypes**: Class modification system

### System-Agnostic Concepts
Despite differences, most systems share:
- Ability scores or attributes
- Character advancement (levels/experience)
- Skills or proficiencies
- Equipment and inventory
- Some form of hit points/health

## OPTIMIZATION CONCEPTS

### MinMax Strategy Types

1. **Single Ability Focus** (SAD - Single Ability Dependent)
   - Maximize one ability score
   - Choose features that key off that ability
   - Example: Dexterity-based Fighter

2. **Multi Ability Balance** (MAD - Multi Ability Dependent)
   - Balance multiple important abilities
   - More complex optimization
   - Example: Monk (needs DEX, WIS, CON)

3. **Action Economy Optimization**
   - Maximize actions per turn
   - Bonus action utilization
   - Reaction opportunities

4. **Resource Efficiency**
   - Long rest vs short rest resources
   - Sustainable vs burst damage
   - Resource recovery mechanisms

### Optimization Constraints
- **Table Variance**: Some groups ban certain combinations
- **Starting Level**: Different strategies for level 1 vs level 10
- **Campaign Type**: Dungeon crawl vs political intrigue
- **Party Composition**: Filling needed roles

## RULE AMBIGUITY HANDLING

### Sources of Ambiguity
1. **Natural Language**: Rules written in prose, not code
2. **Edge Cases**: Unusual combinations not explicitly covered
3. **Version Differences**: Rules change between printings
4. **Designer Intent**: Sometimes conflicts with literal reading

### Resolution Strategy
1. **Check Errata**: Official corrections first
2. **Designer Clarification**: Tweets, interviews, sage advice
3. **Community Consensus**: How most tables play it
4. **Logical Interpretation**: What makes sense mechanically
5. **Conservative Ruling**: When in doubt, choose restrictive interpretation

## VALIDATION PHILOSOPHY

### Strict vs Permissive
Astarion defaults to **strict validation** because:
- Online play often requires RAW (Rules As Written)
- Tournaments need consistency
- New players need clear guidelines

But provides **permissive options** for:
- Home games with house rules
- Experienced groups
- DM discretion scenarios

### Validation Layers
1. **Core Rules**: Always enforced (basic game mechanics)
2. **Optional Rules**: Toggled based on table preferences
3. **House Rules**: Custom modifications
4. **Campaign Settings**: Setting-specific restrictions

## RULE INTERACTION PATTERNS

### Common Interaction Types

1. **Stacking Rules**
   - Same source doesn't stack
   - Different sources usually do
   - Exceptions explicitly stated

2. **Specific vs General**
   - Specific rules override general
   - Class features override basic rules
   - Feats can override class features

3. **Prerequisite Chains**
   - Some features require others
   - Order matters for validation
   - Can create complex dependencies

### Complex Interaction Example
**Scenario**: Elf Wizard taking Bladesinger subclass
- Race provides weapon proficiencies
- Class provides different proficiencies  
- Subclass has racial restriction
- Feats might modify proficiencies

**Validation Needs**:
- Check racial eligibility
- Merge proficiency lists correctly
- Apply restrictions in correct order
- Track source of each proficiency

## SOURCE CITATION IMPORTANCE

### Why Citations Matter
1. **Dispute Resolution**: Players can check the source
2. **Rules Lawyers**: Satisfy those who want proof
3. **Learning Tool**: Helps users understand rules
4. **Version Tracking**: Different printings have different rules

### Citation Format
Standard format: `[Book Abbreviation] p.[page] "[exact quote if relevant]"`
Example: `PHB p.163 "You must have a Strength or Dexterity score of 13 or higher"`

### Citation Challenges
- **Cross-References**: Rules that reference other sections
- **Scattered Rules**: Single concept across multiple pages
- **Implicit Rules**: Things assumed but not stated
- **Conflicting Sources**: When books disagree

## FUTURE RULE HANDLING

### Emerging Patterns
- **Digital-First Rules**: Built for online play
- **Modular Systems**: Pick-and-choose rule modules
- **Living Rules**: Frequently updated via errata
- **AI-Assisted Design**: Rules designed for automation

### Astarion's Adaptability
- **Pattern Learning**: Identify new rule structures
- **Community Feedback**: Incorporate interpretations
- **Publisher Integration**: Direct rule feeds
- **Version Management**: Handle multiple rule versions