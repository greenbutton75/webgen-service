"""
WebGen client — sends snapshots to the remote service, polls, and downloads ZIPs.

Usage examples:
  # Single site (real snapshot):
  python tests/test_client.py --snapshot D:/Work/ML/Rix_sites/SiteSnpashot/out-text/www.appleseedwealth.com/snapshot.md

  # All sites in a directory:
  python tests/test_client.py --dir D:/Work/ML/Rix_sites/SiteSnpashot/out-text

  # Override service URL:
  python tests/test_client.py --url http://207.180.148.74:45070 --snapshot ...

  # Download already-done jobs (by job id):
  python tests/test_client.py --download 5d8185cd-c432-4cf6-88c7-c494c78b9b6f
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_URL = "http://207.180.148.74:45070"
DEFAULT_OUT  = Path(__file__).parent.parent / "test_output"
POLL_INTERVAL = 10   # seconds between status checks
MAX_WAIT      = 3600 # 1h max per job

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"


# ── HTTP helpers ──────────────────────────────────────────────────────────────

def _req(method: str, url: str, body: dict | None = None, timeout: int = 30) -> dict | bytes:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
        ct = r.headers.get("Content-Type", "")
        if "json" in ct:
            return json.loads(raw)
        return raw  # binary (ZIP)


def post(url: str, body: dict) -> dict:
    return _req("POST", url, body)


def get_json(url: str) -> dict | list:
    return _req("GET", url)


def get_binary(url: str) -> bytes:
    return _req("GET", url, timeout=60)


# ── Core actions ──────────────────────────────────────────────────────────────

def submit_job(base_url: str, snapshot_text: str) -> str:
    resp = post(f"{base_url}/start", {"snapshot": snapshot_text})
    return resp["website_id"]


def poll_until_done(base_url: str, job_id: str) -> dict:
    deadline = time.time() + MAX_WAIT
    while time.time() < deadline:
        status = get_json(f"{base_url}/status/{job_id}")
        s = status["status"]
        elapsed = int(time.time() - (time.time() % 1))  # rough

        if s == "done":
            return status
        if s == "error":
            raise RuntimeError(f"Job failed: {status.get('error') or '(no message)'}")

        tokens = status.get("snapshot_tokens", 0)
        domain = status.get("domain", "…")
        print(f"  {DIM}[{job_id[:8]}] {domain} | {s} | {tokens} tokens{RESET}", end="\r")
        time.sleep(POLL_INTERVAL)

    raise TimeoutError(f"Job {job_id} did not finish within {MAX_WAIT}s")


def download_zip(base_url: str, job_id: str, out_dir: Path, domain: str) -> Path:
    raw = get_binary(f"{base_url}/download/{job_id}")
    out_dir.mkdir(parents=True, exist_ok=True)
    safe = domain.replace(".", "_").replace("/", "_") if domain else job_id[:8]
    dest = out_dir / f"{safe}.zip"
    dest.write_bytes(raw)
    return dest


# ── Processing a single snapshot file ────────────────────────────────────────

def process_snapshot(base_url: str, snapshot_path: Path, out_dir: Path) -> None:
    domain = snapshot_path.parent.name
    print(f"\n{BOLD}{CYAN}{domain}{RESET}")
    print(f"  {DIM}{snapshot_path}{RESET}")

    text = snapshot_path.read_text(encoding="utf-8", errors="replace")
    tokens_est = len(text) // 4
    print(f"  Snapshot: {len(text) / 1024:.1f} KB  (~{tokens_est:,} tokens)")

    # Submit
    try:
        job_id = submit_job(base_url, text)
    except Exception as e:
        print(f"  {RED}SUBMIT ERROR: {e}{RESET}")
        return

    print(f"  Job ID: {job_id}")

    # Poll
    try:
        t0 = time.time()
        status = poll_until_done(base_url, job_id)
        elapsed = time.time() - t0
        print(f"\n  {GREEN}Done in {elapsed:.0f}s  |  tokens={status.get('snapshot_tokens')}  strategy={status.get('strategy')}{RESET}")
    except (RuntimeError, TimeoutError) as e:
        print(f"\n  {RED}FAILED: {e}{RESET}")
        return

    # Download
    try:
        zip_path = download_zip(base_url, job_id, out_dir, domain)
        size_kb = zip_path.stat().st_size / 1024
        print(f"  {GREEN}Saved: {zip_path}  ({size_kb:.1f} KB){RESET}")
    except Exception as e:
        print(f"  {RED}DOWNLOAD ERROR: {e}{RESET}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="WebGen test client")
    parser.add_argument("--url", default=DEFAULT_URL, help="Service base URL")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory for ZIPs")
    parser.add_argument("--snapshot", help="Path to a single snapshot.md file")
    parser.add_argument("--dir", help="Directory containing <domain>/snapshot.md files")
    parser.add_argument("--download", help="Download an already-done job by ID")
    parser.add_argument("--jobs", action="store_true", help="List all jobs on the server")
    args = parser.parse_args()

    base_url = args.url.rstrip("/")
    out_dir  = Path(args.out)

    # Health check
    try:
        h = get_json(f"{base_url}/health")
        print(f"{GREEN}Service online: {base_url}{RESET}  ok={h.get('ok')}")
    except Exception as e:
        print(f"{RED}Service unreachable: {e}{RESET}")
        sys.exit(1)

    # --jobs: list
    if args.jobs:
        jobs = get_json(f"{base_url}/jobs")
        print(f"\n{'ID':<38} {'Domain':<35} {'Status':<12} {'Tokens':>8}")
        print("-" * 100)
        for j in jobs:
            c = GREEN if j["status"] == "done" else RED if j["status"] == "error" else YELLOW
            print(f"{j['id']:<38} {(j['domain'] or ''):<35} {c}{j['status']:<12}{RESET} {j['snapshot_tokens']:>8}")
        return

    # --download: just download by id
    if args.download:
        job_id = args.download
        status = get_json(f"{base_url}/status/{job_id}")
        if status["status"] != "done":
            print(f"{YELLOW}Job not done yet: {status['status']}{RESET}")
            return
        domain = status.get("domain", job_id[:8])
        zip_path = download_zip(base_url, job_id, out_dir, domain)
        print(f"{GREEN}Downloaded: {zip_path}{RESET}")
        return

    # --snapshot: single file
    if args.snapshot:
        process_snapshot(base_url, Path(args.snapshot), out_dir)
        return

    # --dir: batch
    if args.dir:
        base = Path(args.dir)
        snapshots = sorted(base.glob("*/snapshot.md"))
        if not snapshots:
            print(f"{RED}No snapshot.md files found in: {base}{RESET}")
            sys.exit(1)
        print(f"Found {len(snapshots)} snapshots in {base}\n")
        for snap in snapshots:
            process_snapshot(base_url, snap, out_dir)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
