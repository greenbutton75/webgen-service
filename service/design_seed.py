import hashlib

STYLES = [
    "minimalist brutalist",
    "warm editorial",
    "dark tech",
    "luxury minimal",
    "corporate clean",
    "glassmorphism",
    "earthy organic",
    "neo-brutalist",
    "fintech precision",
    "startup bold",
    "aurora gradient",
    "monochrome professional",
    "financial advisory premium",
    "data-driven dashboard",
    "bold typographic",
]

LAYOUTS = [
    "asymmetric grid",
    "full-width sections",
    "magazine layout",
    "single column editorial",
    "bento grid",
    "hero-first split",
    "card-dominant",
]

TYPOGRAPHY = [
    "large expressive headings with tight monospace body",
    "serif editorial headlines with clean sans body",
    "geometric sans throughout",
    "mixed serif-sans (headings serif, body sans)",
    "system font stack with bold weight contrast",
    "condensed display headings with generous body spacing",
]

# Fintech/finance-appropriate palette seeds (hue ranges)
# Grouped by feel: cool-professional, warm-premium, dark-tech, earthy
PALETTE_SEEDS = [
    {"hue": 220, "name": "deep navy"},
    {"hue": 195, "name": "teal professional"},
    {"hue": 262, "name": "purple premium"},
    {"hue": 142, "name": "emerald growth"},
    {"hue": 25, "name": "amber warm"},
    {"hue": 0, "name": "crimson bold"},
    {"hue": 174, "name": "mint fresh"},
    {"hue": 210, "name": "steel blue"},
    {"hue": 280, "name": "violet trust"},
    {"hue": 45, "name": "gold luxury"},
    {"hue": 160, "name": "forest sage"},
    {"hue": 200, "name": "ocean depth"},
]


def get_design_seed(domain: str) -> dict:
    h = int(hashlib.md5(domain.encode()).hexdigest(), 16)
    palette = PALETTE_SEEDS[(h >> 4) % len(PALETTE_SEEDS)]
    return {
        "style": STYLES[h % len(STYLES)],
        "layout": LAYOUTS[(h >> 8) % len(LAYOUTS)],
        "typography": TYPOGRAPHY[(h >> 16) % len(TYPOGRAPHY)],
        "accent_hue": palette["hue"],
        "palette_name": palette["name"],
    }
