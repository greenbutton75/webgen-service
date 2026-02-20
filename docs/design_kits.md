# Design Kits - Plan for Design Variability

## Goal
Make sites visually unique while preserving required structure and functionality.

## Problem
The current prompts lock in too many layout and CSS decisions. That yields
consistency, but makes outputs look similar.

## Approach: Design Kits
Create 8-15 "kits" that define visual and layout decisions. Each kit specifies:
- layout rhythm (grid/spacing)
- card style (radius, border, shadow)
- navigation style (background, height, CTA treatment)
- hero treatment (background, overlay, imagery)
- form and search UI (inputs, dropdown cards)
- decorative motifs (lines, rings, gradients, texture)
- typography and spacing scale (head/body sizes and section padding)

### Example kit structure (in `design_seed.py`)
DesignKit = {
  name,
  hero_variant,
  nav_variant,
  card_style,
  form_style,
  search_style,
  section_motif,
  radius,
  shadow,
  spacing
}

## Selection strategy
Pick a kit deterministically by domain hash (1 domain -> 1 style).

## Prompt integration
In `_build_user_prompt`, include:
- "Design Kit: <name>"
- a short bullet list of kit rules (hero, nav, cards, forms, motifs)

Then relax the rigid CSS prescriptions in `prompts/system.txt`, so the kit
meaningfully changes the look.

## Implementation options
1. One `system.txt` + kits (recommended, easiest to maintain).
2. Multiple `system_*.txt` files (harder to maintain).
3. Multiple HTML skeleton variants per section (most variability, more work).

## Pros
- Real visual uniqueness with consistent structure.
- Centralized control and easy expansion.
- Deterministic outputs for a domain.

## Next steps
1. Define 8-12 kits.
2. Add kit selection logic in `design_seed.py`.
3. Update prompt builder to pass kit data.
4. Run batch tests and tune kit rules.
