from __future__ import annotations

import json
import sys
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from templates.base import render
from templates.pages import CONFIG, LOGS, OVERVIEW, PIPELINE, TRAINING

ROOT = Path(__file__).resolve().parent
SRC_PATH = ROOT / "src"

app = FastAPI(title="Emily Pipeline Control")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")


# ── Job tracking ──────────────────────────────────────────────

@dataclass
class Job:
    job_id: str
    kind: str
    status: str
    output: str = ""
    error: str = ""


_jobs: dict[str, Job] = {}


def _run_job(job: Job, target, *args: Any) -> None:
    try:
        job.output = target(*args)
        job.status = "completed"
    except Exception as exc:
        job.error = str(exc)
        job.status = "failed"


def _spawn(target, *args: Any) -> Job:
    job = Job(job_id=str(uuid.uuid4())[:8], kind=target.__name__, status="running")
    _jobs[job.job_id] = job
    threading.Thread(target=_run_job, args=(job, target, *args), daemon=True).start()
    return job


# ── Pipeline operations ───────────────────────────────────────

def _run_pipeline(user_input: str) -> str:
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    from pipeline.contracts.models import RequestEnvelope
    from pipeline.orchestrator.pipeline import EmotivePipeline

    pipeline = EmotivePipeline()
    request = RequestEnvelope(
        request_id=str(uuid.uuid4()),
        user_id="web-user",
        user_input=user_input,
        trace_id=str(uuid.uuid4()),
    )
    result = pipeline.run(request)
    lines = [f"Response: {result.response.text}"]
    if result.response.safety_notes:
        lines.append("Safety notes:")
        for note in result.response.safety_notes:
            lines.append(f"  - {note}")
    lines.append(f"Traces: {len(result.traces)} stages")
    for trace in result.traces:
        lines.append(f"  {trace.stage_name}: {trace.status}")
    return "\n".join(lines)


def _prepare_dataset() -> str:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from dataset_prep import prepare_from_hf
    outputs = prepare_from_hf(ROOT / "dataset")
    lines = ["Dataset preparation complete:"]
    for name, path in outputs.items():
        lines.append(f"  {name}: {path}")
    return "\n".join(lines)


def _train_model() -> str:
    data_path = ROOT / "dataset" / "emotion_train.jsonl"
    output_path = ROOT / "models" / "emotion_model.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found at {data_path}. Run dataset preparation first.")
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    from pipeline.stages.emotion_engine.train_nlp_emotion_model import train_from_jsonl
    saved = train_from_jsonl(data_path, output_path)
    return f"Model saved to {saved}"


# ── Page routes ───────────────────────────────────────────────

def _page(title: str, path: str, content: str) -> HTMLResponse:
    return HTMLResponse(render(title, path, content))


@app.get("/")
async def page_overview():
    return _page("Overview", "/", OVERVIEW)


@app.get("/pipeline")
async def page_pipeline():
    return _page("Pipeline", "/pipeline", PIPELINE)


@app.get("/training")
async def page_training():
    return _page("Training", "/training", TRAINING)


@app.get("/config")
async def page_config():
    return _page("Settings", "/config", CONFIG)


@app.get("/logs")
async def page_logs():
    return _page("Logs", "/logs", LOGS)


# ── API routes ────────────────────────────────────────────────

@app.post("/api/pipeline/run")
async def api_pipeline_run(body: dict[str, Any]):
    user_input = body.get("user_input", "")
    if not user_input.strip():
        return {"error": "user_input is required"}
    job = _spawn(_run_pipeline, user_input)
    return {"job_id": job.job_id, "status": job.status}


@app.post("/api/dataset/prepare")
async def api_dataset_prepare():
    job = _spawn(_prepare_dataset)
    return {"job_id": job.job_id, "status": job.status}


@app.post("/api/model/train")
async def api_model_train():
    job = _spawn(_train_model)
    return {"job_id": job.job_id, "status": job.status}


@app.get("/api/jobs/{job_id}")
async def api_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        return {"error": "job not found"}
    return {"job_id": job.job_id, "kind": job.kind, "status": job.status, "output": job.output, "error": job.error}


@app.get("/api/config")
async def api_config():
    config_path = ROOT / "configs" / "config.json"
    if config_path.exists():
        return json.loads(config_path.read_text(encoding="utf-8"))
    return {"error": "config not found"}


@app.post("/api/config")
async def api_config_update(body: dict[str, Any]):
    config_path = ROOT / "configs" / "config.json"
    current = {}
    if config_path.exists():
        current = json.loads(config_path.read_text(encoding="utf-8"))
    current.update(body)
    config_path.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "updated", "config": current}


@app.get("/api/telemetry")
async def api_telemetry(lines: int = 50):
    log_path = ROOT / "logs" / "pipeline-telemetry.jsonl"
    if not log_path.exists():
        return {"entries": []}
    raw = log_path.read_text(encoding="utf-8").strip().splitlines()
    recent = raw[-lines:] if len(raw) > lines else raw
    entries = []
    for line in recent:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return {"entries": entries}


@app.get("/api/status")
async def api_status():
    return {
        "pipeline": "ready",
        "config_path": str(ROOT / "configs" / "config.json"),
        "model_path": str(ROOT / "models" / "emotion_model.json"),
        "dataset_path": str(ROOT / "dataset"),
        "telemetry_path": str(ROOT / "logs" / "pipeline-telemetry.jsonl"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
