import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from service import db
from service.worker import worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

ADMIN_HTML = Path(os.getenv("WEBGEN_ADMIN_PATH", "admin/index.html"))

app = FastAPI(title="WebGen", version="1.0.0")

db.init_db()


@app.on_event("startup")
async def _startup():
    worker.start()


# ── Client API ────────────────────────────────────────────────────────────────

class StartRequest(BaseModel):
    snapshot: str


@app.post("/start")
async def start(req: StartRequest):
    if not req.snapshot or len(req.snapshot.strip()) < 100:
        raise HTTPException(400, "Snapshot is too short or empty")

    tokens = len(req.snapshot) // 4
    job_id = db.create_job(snapshot_tokens=tokens)
    await worker.enqueue(job_id, req.snapshot)
    return {"website_id": job_id}


@app.get("/status/{job_id}")
async def status(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "status": job["status"],
        "domain": job["domain"],
        "snapshot_tokens": job["snapshot_tokens"],
        "strategy": job["strategy"],
        "error": job["error"],
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }


@app.get("/download/{job_id}")
async def download(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "done":
        raise HTTPException(400, f"Job is not done yet (status: {job['status']})")
    zip_path = Path(job["zip_path"])
    if not zip_path.exists():
        raise HTTPException(404, "ZIP file not found (may have been deleted)")
    filename = f"{job['domain'] or job_id}.zip"
    return FileResponse(zip_path, media_type="application/zip", filename=filename)


# ── Admin API ─────────────────────────────────────────────────────────────────

@app.get("/jobs")
async def list_jobs():
    jobs = db.get_all_jobs()
    return [dict(j) for j in jobs]


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["zip_path"]:
        p = Path(job["zip_path"])
        if p.exists():
            p.unlink()
    db.delete_job(job_id)
    return {"ok": True}


@app.get("/queue")
async def queue_info():
    return {"pending_in_queue": worker.queue_size}


# ── Admin UI ──────────────────────────────────────────────────────────────────

@app.get("/admin", response_class=HTMLResponse)
async def admin():
    if not ADMIN_HTML.exists():
        raise HTTPException(503, "Admin UI not found")
    return ADMIN_HTML.read_text(encoding="utf-8")


@app.get("/health")
async def health():
    return {"ok": True}
