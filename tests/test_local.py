"""
Local test script for WebGen preprocessor and design seed.
Run from the WebGen root directory:

    python tests/test_local.py

Optionally pass a path to out-text directory:
    python tests/test_local.py D:/Work/ML/Rix_sites/SiteSnpashot/out-text

Requires no external packages — only stdlib + service modules.
"""
from __future__ import annotations

import sys
import os
from pathlib import Path

# Allow importing from service/ without installing
sys.path.insert(0, str(Path(__file__).parent.parent))

from service.preprocessor import preprocess, estimate_tokens
from service.design_seed import get_design_seed

# ── Colors for terminal output ────────────────────────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def bar(value: int, max_value: int, width: int = 30) -> str:
    filled = int(width * min(value, max_value) / max_value)
    color = GREEN if value < max_value * 0.6 else YELLOW if value < max_value * 0.9 else RED
    return f"{color}{'#' * filled}{'.' * (width - filled)}{RESET}"


def find_snapshots(base_path: Path) -> list[Path]:
    return sorted(base_path.glob("*/snapshot.md"))


def test_snapshot(snapshot_path: Path) -> dict:
    text = snapshot_path.read_text(encoding="utf-8", errors="replace")
    raw_tokens = estimate_tokens(text)

    result = preprocess(text)
    design = get_design_seed(result.domain) if result.strategy != "error" else None

    return {
        "path": snapshot_path,
        "raw_kb": len(text) / 1024,
        "raw_tokens": raw_tokens,
        "result": result,
        "design": design,
    }


def print_report(data: list[dict]) -> None:
    MAX_DISPLAY_TOKENS = 70_000

    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}  WebGen Preprocessor Test Report{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

    for d in sorted(data, key=lambda x: x["raw_tokens"], reverse=True):
        r = d["result"]
        design = d["design"]

        status_color = GREEN if r.strategy != "error" else RED
        strategy_label = f"[{r.strategy.upper()}]" if r.strategy != "error" else "[ERROR]"
        reduction = (1 - r.tokens / d["raw_tokens"]) * 100 if d["raw_tokens"] > 0 else 0

        print(f"{BOLD}{CYAN}{r.domain or d['path'].parent.name}{RESET}")
        print(f"  {DIM}File: {d['path']}{RESET}")
        print(f"  Raw:      {d['raw_kb']:7.1f} KB  |  {d['raw_tokens']:7,} tokens  "
              f"{bar(d['raw_tokens'], MAX_DISPLAY_TOKENS)}")

        if r.strategy != "error":
            print(f"  Filtered: {' ' * 10}  |  {r.tokens:7,} tokens  "
                  f"{bar(r.tokens, MAX_DISPLAY_TOKENS)}  "
                  f"{GREEN}(-{reduction:.0f}%){RESET}")
            print(f"  Strategy: {status_color}{strategy_label}{RESET}")
            if design:
                print(f"  Design:   style={CYAN}{design['style']}{RESET}  "
                      f"layout={CYAN}{design['layout']}{RESET}  "
                      f"palette={CYAN}{design['palette_name']}{RESET} (hue={design['accent_hue']})")
                print(f"            typo={DIM}{design['typography']}{RESET}")
        else:
            print(f"  {RED}ERROR: {r.error}{RESET}")

        print()

    # Summary
    total = len(data)
    errors = sum(1 for d in data if d["result"].strategy == "error")
    truncated = sum(1 for d in data if d["result"].strategy == "truncated")
    ok = total - errors - truncated

    print(f"{BOLD}{'-' * 80}{RESET}")
    print(f"  Total:     {total}")
    print(f"  {GREEN}OK (single_pass): {ok}{RESET}")
    print(f"  {YELLOW}Truncated:        {truncated}{RESET}")
    print(f"  {RED}Errors:           {errors}{RESET}")

    avg_raw = sum(d["raw_tokens"] for d in data if d["result"].strategy != "error") / max(ok + truncated, 1)
    avg_filt = sum(d["result"].tokens for d in data if d["result"].strategy != "error") / max(ok + truncated, 1)
    if ok + truncated > 0:
        print(f"\n  Avg raw tokens (valid):      {avg_raw:,.0f}")
        print(f"  Avg filtered tokens (valid): {avg_filt:,.0f}  "
              f"({(1 - avg_filt / avg_raw) * 100:.0f}% avg reduction)")

    print(f"{BOLD}{'=' * 80}{RESET}\n")

    # Warn about context limit
    over_limit = [d for d in data if d["result"].tokens > 50_000 and d["result"].strategy != "error"]
    if over_limit:
        print(f"{YELLOW}WARN: {len(over_limit)} site(s) will push LLM to high token counts (>50k filtered):{RESET}")
        for d in over_limit:
            print(f"     {d['result'].domain}: {d['result'].tokens:,} tokens -- may need continuation pass")
        print()


def test_section_templates() -> None:
    """Quick check that section templates load and contain required markers."""
    print(f"{BOLD}Section Template Check{RESET}")
    templates_dir = Path(__file__).parent.parent / "prompts" / "sections"

    required_markers = {
        "news.html": ["{{SITE_DOMAIN}}", "api/get-news", "newsSection()", "x-data"],
        "plan_search_strategy.html": [
            "{{SITE_DOMAIN}}", "api/plan-search", "api/plan-strategy", "planSection()", "x-data"
        ],
    }

    all_ok = True
    for filename, markers in required_markers.items():
        path = templates_dir / filename
        if not path.exists():
            print(f"  {RED}MISS {filename} -- NOT FOUND{RESET}")
            all_ok = False
            continue
        content = path.read_text(encoding="utf-8")
        missing = [m for m in markers if m not in content]
        if missing:
            print(f"  {RED}FAIL {filename} -- missing markers: {missing}{RESET}")
            all_ok = False
        else:
            size_kb = len(content) / 1024
            print(f"  {GREEN}OK   {filename} ({size_kb:.1f} KB){RESET}")

    print()
    return all_ok


def main():
    # Determine snapshots base path
    if len(sys.argv) > 1:
        base = Path(sys.argv[1])
    else:
        # Default: try to find relative to this script
        candidates = [
            Path(__file__).parent.parent.parent / "SiteSnpashot" / "out-text",
            Path("D:/Work/ML/Rix_sites/SiteSnpashot/out-text"),
        ]
        base = next((p for p in candidates if p.exists()), None)

    print(f"{BOLD}WebGen Local Test{RESET}")
    print(f"{DIM}Python: {sys.version.split()[0]}{RESET}\n")

    # 1. Template check
    test_section_templates()

    # 2. Design seed determinism check
    print(f"{BOLD}Design Seed Determinism Check{RESET}")
    domain = "www.appleseedwealth.com"
    d1 = get_design_seed(domain)
    d2 = get_design_seed(domain)
    assert d1 == d2, "Design seed is not deterministic!"
    print(f"  {GREEN}OK  Same domain always gets same seed{RESET}")

    d3 = get_design_seed("www.hbkswealth.com")
    if d3["style"] != d1["style"] or d3["layout"] != d1["layout"]:
        print(f"  {GREEN}OK  Different domains get different seeds{RESET}")
    else:
        print(f"  {YELLOW}WARN Same style+layout for two test domains -- coincidence, check manually{RESET}")
    print()

    # 3. Preprocessor on all snapshots
    if not base or not base.exists():
        print(f"{YELLOW}No snapshot directory found. Pass path as argument:{RESET}")
        print(f"  python tests/test_local.py <path-to-out-text>")
        return

    snapshots = find_snapshots(base)
    if not snapshots:
        print(f"{RED}No snapshot.md files found in: {base}{RESET}")
        return

    print(f"{BOLD}Processing {len(snapshots)} snapshots from:{RESET}")
    print(f"  {DIM}{base}{RESET}\n")

    results = []
    for snap in snapshots:
        print(f"  Processing {snap.parent.name}...", end=" ", flush=True)
        data = test_snapshot(snap)
        r = data["result"]
        if r.strategy == "error":
            print(f"{RED}{r.error}{RESET}")
        else:
            print(f"{GREEN}OK ({r.tokens:,} tokens){RESET}")
        results.append(data)

    print_report(results)

    # 4. Show prompt size estimate (snapshot + templates)
    news_size = estimate_tokens(
        (Path(__file__).parent.parent / "prompts" / "sections" / "news.html").read_text()
    )
    plan_size = estimate_tokens(
        (Path(__file__).parent.parent / "prompts" / "sections" / "plan_search_strategy.html").read_text()
    )
    system_size = estimate_tokens(
        (Path(__file__).parent.parent / "prompts" / "system.txt").read_text()
    )
    template_overhead = news_size + plan_size + system_size

    print(f"{BOLD}Prompt token budget (per request):{RESET}")
    print(f"  System prompt:       {system_size:,} tokens")
    print(f"  News template:       {news_size:,} tokens")
    print(f"  Plan template:       {plan_size:,} tokens")
    print(f"  Total overhead:      {template_overhead:,} tokens")
    print(f"  Max model len:       65,536 tokens")
    print(f"  Available for site:  {65536 - template_overhead - 12288:,} tokens (after reserving 12k for output)")
    print()


if __name__ == "__main__":
    main()
