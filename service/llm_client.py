from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx

from service.design_seed import get_design_seed

logger = logging.getLogger(__name__)

VLLM_URL = os.getenv("WEBGEN_VLLM_URL", "http://localhost:8000")
MODEL_NAME = os.getenv("WEBGEN_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")
MAX_TOKENS = int(os.getenv("WEBGEN_MAX_TOKENS", "10000"))

# Streaming: no read timeout (tokens arrive continuously).
# Connect/write have short timeouts to catch vLLM being down.
STREAM_TIMEOUT = httpx.Timeout(connect=30.0, read=None, write=30.0, pool=30.0)

PROMPTS_DIR = Path(os.getenv("WEBGEN_PROMPTS_DIR", "prompts"))
SYSTEM_PROMPT_PATH = PROMPTS_DIR / "system.txt"
NEWS_TEMPLATE_PATH = PROMPTS_DIR / "sections" / "news.html"
PLAN_SECTION_PATH = PROMPTS_DIR / "sections" / "plan_search_strategy.html"


def _load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _build_user_prompt(domain: str, content: str, design: dict) -> str:
    news_tpl = _load_text(NEWS_TEMPLATE_PATH).replace("{{SITE_DOMAIN}}", domain)
    plan_tpl = _load_text(PLAN_SECTION_PATH).replace("{{SITE_DOMAIN}}", domain)

    return f"""Website domain: {domain}

Design direction for this site:
- Visual style: {design['style']}
- Layout approach: {design['layout']}
- Typography: {design['typography']}
- Font pair: {design['font_hint']}
- Google Fonts URL params: {design['google_fonts']}
- Primary accent hue (HSL): {design['accent_hue']} ({design['palette_name']})

Website content snapshot (Markdown):
---
{content}
---

REQUIRED SECTION 1 — News & AI Briefing (restyle to match your CSS, keep all JS fetch logic exactly as written):
{news_tpl}

REQUIRED SECTION 2 — Retirement Plan Search + Strategy (restyle to match your CSS, keep all JS fetch logic exactly as written):
{plan_tpl}

Now generate the complete HTML file."""


async def _chat(messages: list[dict], max_tokens: int, temperature: float) -> tuple[str, str]:
    """Stream response from vLLM, return (full_content, finish_reason).
    Using streaming avoids ReadTimeout on long generations (10+ min for 32B models).
    """
    chunks: list[str] = []
    finish_reason = "stop"

    async with httpx.AsyncClient(timeout=STREAM_TIMEOUT) as client:
        async with client.stream(
            "POST",
            f"{VLLM_URL}/v1/chat/completions",
            json={
                "model": MODEL_NAME,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
            },
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                payload = line[6:]
                if payload.strip() == "[DONE]":
                    break
                try:
                    data = json.loads(payload)
                    choice = data["choices"][0]
                    delta = choice.get("delta", {})
                    if "content" in delta and delta["content"]:
                        chunks.append(delta["content"])
                    fr = choice.get("finish_reason")
                    if fr:
                        finish_reason = fr
                except (json.JSONDecodeError, KeyError):
                    continue

    return "".join(chunks), finish_reason


async def generate_html(domain: str, content: str) -> str:
    design = get_design_seed(domain)
    system_prompt = _load_text(SYSTEM_PROMPT_PATH)
    user_prompt = _build_user_prompt(domain, content, design)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    logger.info(f"[{domain}] Generating HTML (style={design['style']}, layout={design['layout']})")

    html, finish_reason = await _chat(messages, MAX_TOKENS, temperature=0.7)

    # Strip any markdown code fences the model might add
    html = _strip_code_fences(html)

    if finish_reason == "length":
        logger.warning(f"[{domain}] Output truncated (finish_reason=length), attempting continuation")
        html = await _continue_generation(messages, html)

    return html


async def _continue_generation(original_messages: list[dict], partial_html: str) -> str:
    """Ask the model to continue from where it stopped."""
    continuation_messages = original_messages + [
        {"role": "assistant", "content": partial_html},
        {
            "role": "user",
            "content": (
                "The HTML was cut off. Continue generating exactly from where you stopped. "
                "Output ONLY the remaining HTML — no explanation, no code fences. "
                "End with </body></html>."
            ),
        },
    ]

    continuation, finish_reason = await _chat(
        continuation_messages, max_tokens=4096, temperature=0.0
    )
    continuation = _strip_code_fences(continuation)

    if finish_reason == "length":
        logger.warning("Continuation also truncated — closing tags forcefully")
        # Close any open tags gracefully
        if "</body>" not in continuation:
            continuation += "\n</body>"
        if "</html>" not in continuation:
            continuation += "\n</html>"

    return partial_html + continuation


def _strip_code_fences(text: str) -> str:
    """Remove ```html ... ``` wrappers if the model added them."""
    text = text.strip()
    if text.startswith("```"):
        # Remove opening fence
        text = text.split("\n", 1)[-1] if "\n" in text else text
    if text.endswith("```"):
        text = text.rsplit("```", 1)[0]
    return text.strip()
