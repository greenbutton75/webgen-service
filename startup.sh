#!/bin/bash
set -e

REPO="greenbutton75/webgen-service"
BRANCH="main"
MODEL_ID="${WEBGEN_MODEL:-Qwen/Qwen2.5-Coder-32B-Instruct-AWQ}"
GPU_COUNT="${WEBGEN_GPU_COUNT:-2}"
MAX_MODEL_LEN="${WEBGEN_MAX_MODEL_LEN:-65536}"
DATA_DIR="${WEBGEN_DATA_DIR:-/workspace/data}"
SERVICE_PORT="${WEBGEN_PORT:-7860}"
VLLM_PORT="${WEBGEN_VLLM_PORT:-8000}"

# ── Load env vars from Vast.ai template ───────────────────────────────────────
env | grep -E '^(HF_TOKEN|WEBGEN_)' >> /etc/webgen.env 2>/dev/null || true
set -a; source /etc/webgen.env 2>/dev/null || true; set +a

if [ -z "$HF_TOKEN" ]; then
  echo "ERROR: HF_TOKEN is not set. Add it to Vast.ai environment variables."
  exit 1
fi

# ── System deps ───────────────────────────────────────────────────────────────
apt-get update -qq && apt-get install -y -qq git curl python3-pip python3-venv

# ── Python deps ───────────────────────────────────────────────────────────────
pip install -q --upgrade pip
pip install -q vllm
pip install -q fastapi "uvicorn[standard]" httpx python-multipart aiofiles

# ── Install HF CLI ────────────────────────────────────────────────────────────
pip install -q "huggingface_hub[cli]"

# ── Clone / update service code ───────────────────────────────────────────────
WORKDIR="/workspace/webgen"
if [ -d "$WORKDIR/.git" ]; then
  echo "Updating repo..."
  cd "$WORKDIR" && git pull --ff-only
else
  echo "Cloning repo..."
  git clone --branch main --single-branch "https://github.com/${REPO}.git" "$WORKDIR"
fi
cd "$WORKDIR"

# ── Download model ────────────────────────────────────────────────────────────
MODEL_DIR="/workspace/model"
if [ ! -d "$MODEL_DIR/config.json" ]; then
  echo "Downloading model: $MODEL_ID ..."
  huggingface-cli download "$MODEL_ID" \
    --token "$HF_TOKEN" \
    --local-dir "$MODEL_DIR" \
    --local-dir-use-symlinks False
else
  echo "Model already present at $MODEL_DIR"
fi

mkdir -p "$DATA_DIR/results"

# ── Start vLLM ────────────────────────────────────────────────────────────────
echo "Starting vLLM on port $VLLM_PORT ..."
python -m vllm.entrypoints.openai.api_server \
  --model "$MODEL_DIR" \
  --quantization awq \
  --tensor-parallel-size "$GPU_COUNT" \
  --max-model-len "$MAX_MODEL_LEN" \
  --gpu-memory-utilization 0.92 \
  --dtype half \
  --port "$VLLM_PORT" \
  --served-model-name "webgen-model" \
  > "$DATA_DIR/vllm.log" 2>&1 &

VLLM_PID=$!
echo "vLLM PID: $VLLM_PID"

# ── Wait for vLLM to be ready ─────────────────────────────────────────────────
echo "Waiting for vLLM health check..."
for i in $(seq 1 90); do
  if curl -sf "http://localhost:${VLLM_PORT}/health" > /dev/null 2>&1; then
    echo "vLLM is ready (${i} * 10s elapsed)"
    break
  fi
  if ! kill -0 $VLLM_PID 2>/dev/null; then
    echo "ERROR: vLLM process died. Check $DATA_DIR/vllm.log"
    tail -50 "$DATA_DIR/vllm.log"
    exit 1
  fi
  echo "  ... waiting ($i/90)"
  sleep 10
done

# ── Set env for FastAPI service ───────────────────────────────────────────────
export WEBGEN_DATA_DIR="$DATA_DIR"
export WEBGEN_VLLM_URL="http://localhost:${VLLM_PORT}"
export WEBGEN_MODEL="webgen-model"

# ── Start FastAPI service ─────────────────────────────────────────────────────
echo "Starting WebGen service on port $SERVICE_PORT ..."
cd "$WORKDIR"
uvicorn service.main:app \
  --host 0.0.0.0 \
  --port "$SERVICE_PORT" \
  --workers 1 \
  --log-level info
