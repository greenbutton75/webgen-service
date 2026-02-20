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

# Each entry: label (passed to LLM) + google_fonts hint for <link> href
TYPOGRAPHY = [
    {
        "label": "large expressive headings with tight monospace labels",
        "fonts": "Playfair+Display:ital,wght@0,700;0,900;1,700&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=DM+Mono:wght@300;400",
        "hint": "heading=Playfair Display, body=Cormorant Garamond, labels=DM Mono",
    },
    {
        "label": "serif editorial headlines with clean sans body",
        "fonts": "Playfair+Display:ital,wght@0,700;0,900;1,700&family=Inter:wght@300;400;500&family=DM+Mono:wght@400",
        "hint": "heading=Playfair Display, body=Inter, labels=DM Mono",
    },
    {
        "label": "geometric sans throughout with bold weight contrast",
        "fonts": "Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500&family=DM+Mono:wght@400",
        "hint": "heading=Space Grotesk, body=Inter, labels=DM Mono",
    },
    {
        "label": "mixed serif-sans premium",
        "fonts": "Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Plus+Jakarta+Sans:wght@400;500;600&family=DM+Mono:wght@400",
        "hint": "heading=Cormorant Garamond, body=Plus Jakarta Sans, labels=DM Mono",
    },
    {
        "label": "modern sans with bold display contrast",
        "fonts": "Plus+Jakarta+Sans:wght@400;500;700;800&family=Inter:wght@300;400;500&family=DM+Mono:wght@400",
        "hint": "heading=Plus Jakarta Sans, body=Inter, labels=DM Mono",
    },
    {
        "label": "condensed display headings with generous body spacing",
        "fonts": "Barlow+Condensed:wght@600;700;900&family=Inter:wght@300;400;500&family=DM+Mono:wght@400",
        "hint": "heading=Barlow Condensed, body=Inter, labels=DM Mono",
    },
]

# Fintech/finance-appropriate palette seeds (hue ranges)
PALETTE_SEEDS = [
    {"hue": 220, "name": "deep navy"},
    {"hue": 195, "name": "teal professional"},
    {"hue": 262, "name": "purple premium"},
    {"hue": 142, "name": "emerald growth"},
    {"hue": 25,  "name": "amber warm"},
    {"hue": 0,   "name": "crimson bold"},
    {"hue": 174, "name": "mint fresh"},
    {"hue": 210, "name": "steel blue"},
    {"hue": 280, "name": "violet trust"},
    {"hue": 45,  "name": "gold luxury"},
    {"hue": 160, "name": "forest sage"},
    {"hue": 200, "name": "ocean depth"},
]


def get_design_seed(domain: str) -> dict:
    h = int(hashlib.md5(domain.encode()).hexdigest(), 16)
    palette = PALETTE_SEEDS[(h >> 4) % len(PALETTE_SEEDS)]
    typo = TYPOGRAPHY[(h >> 16) % len(TYPOGRAPHY)]
    return {
        "style":       STYLES[h % len(STYLES)],
        "layout":      LAYOUTS[(h >> 8) % len(LAYOUTS)],
        "typography":  typo["label"],
        "font_hint":   typo["hint"],
        "google_fonts": typo["fonts"],
        "accent_hue":  palette["hue"],
        "palette_name": palette["name"],
    }
