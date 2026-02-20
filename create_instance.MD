# Vast.ai Instance — Deploy Guide

## 1. Поиск инстанса

На [cloud.vast.ai](https://cloud.vast.ai) → **Rent** → фильтры:

| Параметр | Значение |
|---|---|
| GPU | **1× A100 SXM4 80GB** (предпочтительно) или 2× A100 40GB PCIe |
| Disk | **80–100 GB** |
| CUDA | 12.1+ |

Для 1× A100 80GB ищи именно `A100 SXM4 80GB` — NVLink, больший VRAM, проще конфигурировать.

---

## 2. Docker Image

В UI выбери шаблон:
```
pytorch/pytorch:2.4.0-cuda12.1-cudnn9-devel
```
Или **PyTorch** → последняя версия с CUDA 12.1.  
Это важно — `pip install vllm` займёт 3 мин вместо 15.

---

## 3. Disk

**80 GB** (модель ~18GB + vLLM/torch ~15GB + ОС ~15GB + данные ~2GB)

---

## 4. Open Ports

```
7860/tcp
```
Порт 8000 (vLLM) — только внутренний, не открывать.

---

## 5. Environment Variables

```
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxxxxxx
WEBGEN_GPU_COUNT=1
```

> **1× A100 80GB** → `WEBGEN_GPU_COUNT=1`  
> **2× A100 40GB** → `WEBGEN_GPU_COUNT=2`  
> `WEBGEN_MAX_MODEL_LEN` не указывать — дефолт 32768 (нативный лимит модели)

---

## 6. Startup Script

Вставить в поле **On-start script** (361 символ, лимит 2000):

```bash
#!/bin/bash
set -e
command -v curl >/dev/null 2>&1 || (apt-get update -qq && apt-get install -y -qq curl)
REPO="greenbutton75/webgen-service"
URL="https://raw.githubusercontent.com/${REPO}/main/startup.sh?ts=$(date +%s)"
curl -fsSL -H "Cache-Control: no-cache" -H "Pragma: no-cache" "$URL" -o /tmp/startup.sh
chmod +x /tmp/startup.sh
exec /tmp/startup.sh
```

---

## 7. Таймлайн после старта

| Время | Что происходит |
|---|---|
| 0–3 мин | apt-get, pip install vllm + fastapi, git clone репо |
| 3–15 мин | Загрузка модели с HuggingFace (~18 GB) |
| 15–20 мин | vLLM загружает веса в GPU VRAM |
| ~20 мин | FastAPI стартует на порту 7860 ✓ |

Логи: Vast.ai console → вкладка **Logs** на инстансе.

---

## 8. Проверить запуск

```bash
# Health check
curl http://<vast_ip>:<mapped_port>/health
# → {"ok": true}

# Admin UI
open http://<vast_ip>:<mapped_port>/admin
```

Маппинг портов смотри в колонке **SSH/Ports** в Vast.ai console:  
`123.45.67.89:XXXXX → 7860`

---

## 9. BASE_URL для клиентского скрипта

```python
BASE_URL = "http://<vast_ip>:<mapped_port>"
```

---

## Важно про данные

ZIP файлы хранятся в `/workspace/data/results` на инстансе.

| Действие | Данные |
|---|---|
| **Stop** (остановить) | ✅ Сохраняются |
| **Destroy** (удалить) | ❌ Теряются |

Скачивай ZIPs сразу или настрой бэкап на S3/R2.

---

## Обновить код без пересоздания инстанса

SSH в инстанс и:
```bash
cd /workspace/webgen
git pull
# Перезапустить uvicorn (найти PID или просто kill -HUP)
pkill -f "uvicorn service.main:app"
cd /workspace/webgen && uvicorn service.main:app --host 0.0.0.0 --port 7860 --workers 1 &
```
