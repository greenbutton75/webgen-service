from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

# Model native max: 32768 tokens
# Fixed overhead (system prompt + section templates): ~5000 tokens
# Output reserve: 10000 tokens
# Available for site content: 32768 - 5000 - 10000 = 17768 → safe limit 16000
MAX_TOKENS_SINGLE_PASS = 16_000
MAX_TOKENS_HARD_LIMIT = 16_000


@dataclass
class PreprocessResult:
    domain: str
    content: str
    tokens: int
    strategy: str  # "single_pass" | "truncated" | "error"
    error: Optional[str] = None


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def extract_domain(text: str) -> str:
    # First line: "# www.example.com"
    m = re.match(r"^#\s*([\w.-]+)", text.strip())
    if m:
        return m.group(1)
    # Fallback: Source header
    m = re.search(r"Source:\s*https?://(?:www\.)?([\w.-]+)", text)
    if m:
        return m.group(1)
    return "unknown"


def is_blocked_snapshot(text: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason)."""
    stripped = text.strip()

    if re.search(r"BLOCKED \(Cloudflare\)", stripped):
        return True, "Site is blocked by Cloudflare"

    # Count meaningful content lines (not headers, not list items, not blank)
    lines = stripped.split("\n")
    content_lines = [
        l for l in lines
        if l.strip()
        and not l.startswith("#")
        and not l.startswith("-")
        and not l.startswith("|")
        and len(l.strip()) > 20
    ]
    if len(content_lines) < 5:
        return True, "Snapshot has no meaningful content (likely blocked or empty)"

    return False, ""


def split_into_page_sections(text: str) -> list[str]:
    """Split at '## PageTitle' markers (page boundaries in snapshot format)."""
    # The header block (before first ##) is metadata — keep as first section
    parts = re.split(r"\n(?=## )", text)
    return [p.strip() for p in parts if p.strip()]


def filter_failed_pages(sections: list[str]) -> list[str]:
    return [s for s in sections if not re.match(r"^## FAILED:", s)]


def dedup_pages(sections: list[str]) -> list[str]:
    """Remove pages with near-identical content (e.g. home page listed twice)."""
    seen: set[str] = set()
    unique: list[str] = []
    for sec in sections:
        # Fingerprint: first 400 chars of content (skip the ## header line)
        lines = sec.split("\n")
        content_start = "\n".join(lines[2:])[:400].strip()
        if content_start not in seen:
            seen.add(content_start)
            unique.append(sec)
    return unique


def strip_repeated_nav(sections: list[str]) -> list[str]:
    """
    Navigation link blocks repeat on every page.
    Keep them only in the first page section; strip from the rest.
    Nav pattern: multiple lines that are short markdown links.
    """
    if len(sections) <= 1:
        return sections

    # Pattern for a nav/menu block: 3+ consecutive short link lines
    nav_block_re = re.compile(
        r"(\n[-*]?\s*\[.{1,60}\]\(.{1,200}\)\s*){3,}", re.MULTILINE
    )

    result = [sections[0]]  # keep first section as-is
    for sec in sections[1:]:
        cleaned = nav_block_re.sub("\n", sec)
        result.append(cleaned)
    return result


def page_priority(section: str) -> int:
    """Lower = higher priority for truncation decisions."""
    s = section.lower()

    # Detect the source URL depth
    m = re.search(r"source:\s*https?://[^\s]+", s)
    if m:
        url = m.group(0)
        depth = url.count("/") - 2  # subtract protocol slashes
        if depth <= 1:
            return 0  # root page

    if any(k in s for k in ["service", "about", "who we are", "our team", "what we do", "approach"]):
        return 1
    if any(k in s for k in ["contact", "reach out", "location", "office"]):
        return 2
    if any(k in s for k in ["blog", "article", "news", "insight", "resource", "case study"]):
        return 3
    if any(k in s for k in ["terms", "privacy", "legal", "disclaimer", "career", "job opening"]):
        return 5
    return 4


def truncate_sections(sections: list[str], max_tokens: int) -> list[str]:
    """Keep highest-priority sections up to token budget."""
    sorted_secs = sorted(sections, key=page_priority)
    result: list[str] = []
    total = 0
    for sec in sorted_secs:
        t = estimate_tokens(sec)
        if total + t > max_tokens:
            # If we have nothing yet, at least include a truncated version of this section
            if not result:
                result.append(sec[: max_tokens * 4])
            break
        result.append(sec)
        total += t
    # Re-sort by original order for coherent reading
    order = {id(s): i for i, s in enumerate(sections)}
    result.sort(key=lambda s: order.get(id(s), 999))
    return result


def preprocess(snapshot_text: str) -> PreprocessResult:
    domain = extract_domain(snapshot_text)

    blocked, reason = is_blocked_snapshot(snapshot_text)
    if blocked:
        return PreprocessResult(
            domain=domain,
            content="",
            tokens=0,
            strategy="error",
            error=reason,
        )

    sections = split_into_page_sections(snapshot_text)
    sections = filter_failed_pages(sections)
    sections = dedup_pages(sections)
    sections = strip_repeated_nav(sections)

    tokens = estimate_tokens("\n\n".join(sections))

    if tokens > MAX_TOKENS_HARD_LIMIT:
        sections = truncate_sections(sections, MAX_TOKENS_HARD_LIMIT)
        strategy = "truncated"
    else:
        strategy = "single_pass"

    content = "\n\n".join(sections)
    final_tokens = estimate_tokens(content)

    return PreprocessResult(
        domain=domain,
        content=content,
        tokens=final_tokens,
        strategy=strategy,
    )
