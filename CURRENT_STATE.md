# WebGen — Current State (2026-02-20, evening)

## Repo
https://github.com/greenbutton75/webgen-service (branch: main)

## Vast.ai Instance
- IP: 207.180.148.74
- Port mapping: 45070 → 7860 (FastAPI)
- GPU: 1× A100 80GB SXM4
- Service URL: http://207.180.148.74:45070

## What's Running
- vLLM: port 8000, PID=3650, **awq_marlin + bfloat16** (fast!)
  - Command: `python -m vllm.entrypoints.openai.api_server --model /workspace/model --quantization awq_marlin --tensor-parallel-size 1 --max-model-len 32768 --gpu-memory-utilization 0.92 --dtype bfloat16 --port 8000 --served-model-name webgen-model`
  - Log: /workspace/data/vllm_new.log
- FastAPI: port 7860, PID=2303, /workspace/webgen
  - Log: /workspace/data/fastapi.log
- Data: /workspace/data/results/ (ZIPs), /workspace/data/jobs.db (SQLite)

## Generation Speed (solved)
- **Before fix**: 4.3 t/s (awq kernel, slow) → 20+ min per site
- **After fix**: 60 t/s (awq_marlin kernel) → **~3 min per site** (hot start)
- Root cause: model was started with `--quantization awq` despite supporting `awq_marlin`
  The log warned: "you specified quantization=awq explicitly, so forcing awq"
- Fix: use `--quantization awq_marlin --dtype bfloat16`

## startup.sh — Clean Instance Will Work Correctly
- ✅ `--quantization awq_marlin` — fast kernel
- ✅ `--dtype bfloat16` — optimal for A100
- ✅ `GPU_COUNT` defaults to 1 (was 2, now fixed)
- ✅ `vllm==0.15.1` pinned (was unversioned)
- ✅ `max-model-len 32768` (was 65536, fixed earlier)
- ⚠️ On first clean start: model download (~18 GB) + CUDA graph compile (~2 min) = cold start ~10-15 min total

## Quality Status (work in progress)
### Issues fixed:
- Dropped Tailwind → pure custom CSS
- Added Google Fonts (per style: Playfair/Cormorant, Space Grotesk, Barlow Condensed, etc.)
- Fixed `rgba(var(--color))` → `hsla(var(--h), var(--s), var(--l), alpha)` pattern
- Section templates (news.html, plan_search_strategy.html) rewritten to BEM CSS classes
  (no more Tailwind classes in templates that break without CDN)

### Current quality issues (being worked on):
- `fade-up` CSS class defined but not applied to HTML elements → no scroll animations
- Hero missing: geo-ring decorative circles, scroll indicator, stats
- Mission/Location/Contact render as single column instead of 2-col grid
- Fake content generated when snapshot is minimal ("Client Name 1", "100+ Years")
- DM Mono font used in CSS but not always loaded in Google Fonts link

### Latest fix (system.txt rewrite):
- Added **concrete HTML skeletons** for every section (hero, mission, services, process, location, contact)
- Explicitly lists which elements need `fade-up` class
- Hero geo-rings (3 concentric circles) now in mandatory HTML structure
- Scroll indicator HTML structure specified
- 2-column grid layouts explicitly required for mission/location/contact
- Services `::before` watermark text ("SERVICES" at 18rem opacity 0.02) specified

## Token Budget (32k model)
- Model max: 32768 tokens
- Fixed overhead (system prompt ~1800t + 2 section templates ~1200t): ~3000 tokens
- Output reserve: 10000 tokens
- Available for site content: ~19000 tokens
- preprocessor.py: MAX_TOKENS = 16000

## Architecture
- POST /start → asyncio queue → single worker → preprocessor → vLLM streaming → postprocessor → ZIP
- GET /status/{id}, GET /download/{id}, GET /admin, GET /jobs, DELETE /jobs/{id}
- SQLite at /workspace/data/jobs.db
- ZIPs at /workspace/data/results/{job_id}.zip

## Design System
- Deterministic per domain via MD5(domain) hash
- 15 styles, 7 layouts, 6 typography options (each with font_hint + google_fonts URL), 12 palettes
- service/design_seed.py — now outputs font_hint and google_fonts fields

## Section Templates
- prompts/sections/news.html → BEM classes, calls /api/get-news
- prompts/sections/plan_search_strategy.html → BEM classes, calls /api/plan-search + /api/plan-strategy
- {{SITE_DOMAIN}} substituted in llm_client.py before sending to LLM

## Files Changed Since Last Known Good State
All committed and pushed to main:
- prompts/system.txt — major rewrite (pure CSS, HTML skeletons, font rules, rgba fix)
- prompts/sections/news.html — rewritten to BEM classes (no Tailwind)
- prompts/sections/plan_search_strategy.html — rewritten to BEM classes (no Tailwind)
- service/design_seed.py — added font_hint, google_fonts fields per typography style
- service/llm_client.py — passes font_hint and google_fonts to user prompt
- startup.sh — awq_marlin, bfloat16, GPU_COUNT=1 default, vllm==0.15.1 pinned
- tests/test_client.py — new batch client script

## Manual Restart on Current Instance (if needed)
```bash
# FastAPI (if down):
cd /workspace/webgen && git pull origin main
export WEBGEN_DATA_DIR=/workspace/data WEBGEN_VLLM_URL=http://localhost:8000 WEBGEN_MODEL=webgen-model
nohup uvicorn service.main:app --host 0.0.0.0 --port 7860 --workers 1 --log-level info \
  >> /workspace/data/fastapi.log 2>&1 &

# vLLM (if down):
nohup python -m vllm.entrypoints.openai.api_server \
  --model /workspace/model --quantization awq_marlin \
  --tensor-parallel-size 1 --max-model-len 32768 \
  --gpu-memory-utilization 0.92 --dtype bfloat16 \
  --port 8000 --served-model-name webgen-model \
  > /workspace/data/vllm_new.log 2>&1 &
```

## Next Steps
1. Test new system.txt generation — check if HTML skeletons are followed
2. Download result, open in browser, compare to index_claude.html reference
3. If animations/layout still broken → consider few-shot example approach (inject sample HTML into prompt)
4. Test with REAL snapshot: D:\Work\ML\Rix_sites\SiteSnpashot\out-text\www.appleseedwealth.com\snapshot.md
   ```powershell
   python tests/test_client.py --snapshot "D:\Work\ML\Rix_sites\SiteSnpashot\out-text\www.appleseedwealth.com\snapshot.md"
   ```
5. If quality OK → destroy instance, create fresh one (startup.sh will run automatically)
6. Batch test: multiple domains via `--dir` flag of test_client.py

## Speed Improvement Options (if 3 min is too slow)
- Switch to 14B model: Qwen/Qwen2.5-Coder-14B-Instruct-AWQ → ~1.5 min, slight quality drop
- H100 SXM5 instance on Vast.ai → ~1.5 min, same quality, ~$3.5-4/h vs $2/h
- Reduce MAX_TOKENS from 10000 to 7000 → ~2 min
- Multiple instances with load balancing → parallel processing
