# WebGen — Current State (2026-02-20)

## Repo
https://github.com/greenbutton75/webgen-service (branch: main)

## Vast.ai Instance
- IP: 207.180.148.74
- Port mapping: 45070 → 7860 (FastAPI)
- GPU: 1× A100 80GB
- Service URL: http://207.180.148.74:45070

## What's Running
- vLLM: port 8000, model=webgen-model (Qwen2.5-Coder-32B-Instruct-AWQ, max_model_len=32768)
- FastAPI: port 7860, /workspace/webgen
- Logs: /workspace/data/fastapi.log, /workspace/data/vllm.log
- Data: /workspace/data/results/ (ZIPs), /workspace/data/jobs.db (SQLite)

## Current Status
First test job running (appleseedwealth.com), processing since ~09:01 UTC.
Waiting for Done. First request cold start = 15-20 min (CUDA graph compile).
Subsequent requests = 3-5 min.

## Startup on Instance (manual, since startup.sh not fully run)
```bash
cd /workspace/webgen && git pull origin main
export WEBGEN_DATA_DIR=/workspace/data
export WEBGEN_VLLM_URL=http://localhost:8000
export WEBGEN_MODEL=webgen-model
nohup uvicorn service.main:app --host 0.0.0.0 --port 7860 --workers 1 --log-level info \
  > /workspace/data/fastapi.log 2>&1 &
```

## Known Issues Fixed
- max_model_len was 65536, model supports 32768 → fixed in startup.sh
- ReadTimeout on long generation → fixed with httpx streaming in llm_client.py
- Python 3.8 type hints (list[str] etc) → fixed with `from __future__ import annotations`
- Unicode chars in test_local.py on Windows cp1251 → fixed with ASCII

## Token Budget (32k model)
- Model max: 32768 tokens
- Fixed overhead (system prompt + 2 section templates): ~5000 tokens  
- Output reserve: 10000 tokens
- Available for site content: ~17000 tokens
- preprocessor.py: MAX_TOKENS_SINGLE_PASS = MAX_TOKENS_HARD_LIMIT = 16000

## Architecture
- POST /start → asyncio queue → single worker → preprocessor → vLLM (streaming) → postprocessor → ZIP
- GET /status/{id}, GET /download/{id}, GET /admin, GET /jobs, DELETE /jobs/{id}
- SQLite at /workspace/data/jobs.db
- ZIPs at /workspace/data/results/{job_id}.zip

## Design System
- Deterministic per domain via MD5(domain) hash
- 15 styles, 7 layouts, 6 typography options, 12 palettes
- service/design_seed.py

## Section Templates
- prompts/sections/news.html → calls /api/get-news
- prompts/sections/plan_search_strategy.html → calls /api/plan-search + /api/plan-strategy
- {{SITE_DOMAIN}} is substituted in llm_client.py before sending to LLM

## Next Steps After First Test Job Completes
1. Download and inspect generated index.html
2. Check all 3 required sections present (api/get-news, api/plan-search, api/plan-strategy)
3. Open in browser, check design quality
4. Run test with real snapshot: D:\Work\ML\Rix_sites\SiteSnpashot\out-text\www.appleseedwealth.com\snapshot.md
5. Write client script (test_client.py) to batch-send snapshots from Windows
6. If quality OK → destroy this instance and create fresh one (startup.sh will run automatically)
7. Fix startup.sh issues (it ran but vLLM crashed on first attempt due to max_model_len)

## Files Modified Since Last Commit (need push)
- service/llm_client.py (streaming fix) ← COMMITTED, needs git push
- CURRENT_STATE.md ← this file
