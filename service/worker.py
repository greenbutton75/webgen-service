from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path

from service import db
from service.llm_client import generate_html
from service.postprocessor import postprocess
from service.preprocessor import preprocess

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(os.getenv("WEBGEN_DATA_DIR", "/workspace/data")) / "results"


async def _process_job(job_id: str, snapshot_text: str) -> None:
    try:
        db.update_job(job_id, status="processing")

        # ── 1. Preprocess ──────────────────────────────────────────────────────
        prep = preprocess(snapshot_text)

        if prep.strategy == "error":
            db.update_job(job_id, status="error", error=prep.error, domain=prep.domain)
            logger.warning(f"[{job_id}] Preprocessing failed: {prep.error}")
            return

        logger.info(
            f"[{job_id}] domain={prep.domain} tokens={prep.tokens} strategy={prep.strategy}"
        )
        db.update_job(
            job_id,
            domain=prep.domain,
            snapshot_tokens=prep.tokens,
            strategy=prep.strategy,
        )

        # ── 2. Generate HTML ───────────────────────────────────────────────────
        html = await generate_html(prep.domain, prep.content)

        # ── 3. Postprocess & pack ──────────────────────────────────────────────
        zip_path, warnings = postprocess(html, prep.domain, job_id, OUTPUT_DIR)

        if warnings:
            logger.warning(f"[{job_id}] Postprocess warnings: {warnings}")

        db.update_job(job_id, status="done", zip_path=str(zip_path))
        logger.info(f"[{job_id}] Done ✓")

    except Exception as exc:
        logger.exception(f"[{job_id}] Unhandled error")
        db.update_job(job_id, status="error", error=str(exc)[:1000])


class JobWorker:
    """Single asyncio worker — processes one job at a time."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[tuple[str, str]] = asyncio.Queue()
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.create_task(self._run(), name="webgen-worker")
        logger.info("Job worker started")

    async def enqueue(self, job_id: str, snapshot_text: str) -> None:
        await self._queue.put((job_id, snapshot_text))
        logger.info(f"[{job_id}] Enqueued (queue size: {self._queue.qsize()})")

    async def _run(self) -> None:
        while True:
            job_id, snapshot_text = await self._queue.get()
            try:
                await _process_job(job_id, snapshot_text)
            finally:
                self._queue.task_done()

    @property
    def queue_size(self) -> int:
        return self._queue.qsize()


worker = JobWorker()
