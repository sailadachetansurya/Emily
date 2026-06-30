from __future__ import annotations

import json
import subprocess
import sys
import threading
import traceback
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
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

PIPELINE_STAGES = [
    "input_gateway",
    "emotion_perception",
    "dual_memory",
    "policy_mapper",
    "prompt_constructor",
    "reasoning_loop",
    "llm_generation",
    "output_pruning",
]


# ── Error reporting ───────────────────────────────────────────

@dataclass
class ErrorDetail:
    stage: str = ""
    part: str = ""
    detail: str = ""
    hint: str = ""
    error_type: str = ""
    traceback: str = ""


def _extract_error(exc: Exception) -> ErrorDetail:
    err = ErrorDetail(error_type=type(exc).__name__, detail=str(exc))
    for attr in ("stage", "part", "hint"):
        if hasattr(exc, attr):
            setattr(err, attr, getattr(exc, attr))
    err.traceback = traceback.format_exc()
    return err


# ── Job tracking ──────────────────────────────────────────────

@dataclass
class Job:
    job_id: str
    kind: str
    status: str
    output: str = ""
    error: str = ""
    error_detail: ErrorDetail | None = None
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0
    current_stage: str = ""
    stages_completed: list[str] = field(default_factory=list)
    result_data: dict[str, Any] = field(default_factory=dict)


_jobs: dict[str, Job] = {}


def _run_job(job: Job, target, *args: Any) -> None:
    start = datetime.now(timezone.utc)
    job.started_at = start.isoformat()
    try:
        job.output = target(job, *args)
        job.status = "completed"
    except Exception as exc:
        job.error = str(exc)
        job.error_detail = _extract_error(exc)
        job.status = "failed"
    finally:
        end = datetime.now(timezone.utc)
        job.finished_at = end.isoformat()
        job.duration_ms = int((end - start).total_seconds() * 1000)
        job.current_stage = ""


def _spawn(target, *args: Any) -> Job:
    job = Job(
        job_id=str(uuid.uuid4())[:8],
        kind=target.__name__,
        status="running",
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    _jobs[job.job_id] = job
    threading.Thread(target=_run_job, args=(job, target, *args), daemon=True).start()
    return job


def _job_to_dict(job: Job) -> dict[str, Any]:
    d = {
        "job_id": job.job_id,
        "kind": job.kind,
        "status": job.status,
        "output": job.output,
        "error": job.error,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "duration_ms": job.duration_ms,
        "current_stage": job.current_stage,
        "stages_completed": job.stages_completed,
        "stages_total": len(PIPELINE_STAGES),
        "result_data": job.result_data,
    }
    if job.error_detail:
        d["error_detail"] = asdict(job.error_detail)
    return d


# ── Summary writer ────────────────────────────────────────────

def _write_summary(user_input: str, result: Any) -> None:
    summary_path = ROOT / "Summary.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        f"\n## Pipeline Run — {now}\n",
        f"**Input:** {user_input}\n",
        f"**Response:** {result.response.text}\n",
    ]
    if result.response.safety_notes:
        lines.append("**Safety notes:**\n")
        for note in result.response.safety_notes:
            lines.append(f"- {note}")
        lines.append("")
    lines.append(f"**Stages ({len(result.traces)}):**\n")
    lines.append("| Stage | Status |")
    lines.append("|---|---|")
    for trace in result.traces:
        lines.append(f"| {trace.stage_name} | {trace.status} |")
    lines.append("")
    lines.append("---\n")
    with summary_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── Pipeline operations ───────────────────────────────────────

def _run_pipeline(job: Job, user_input: str) -> str:
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    from pipeline.contracts.models import RequestEnvelope
    from pipeline.orchestrator.pipeline import EmotivePipeline

    def on_stage(stage_name: str) -> None:
        job.current_stage = stage_name

    pipeline = EmotivePipeline(stage_callback=on_stage)
    request = RequestEnvelope(
        request_id=str(uuid.uuid4()),
        user_id="web-user",
        user_input=user_input,
        trace_id=str(uuid.uuid4()),
    )
    result = pipeline.run(request)
    _write_summary(user_input, result)

    job.result_data = {
        "response": result.response.text,
        "safety_notes": result.response.safety_notes,
        "traces": [{"stage": t.stage_name, "status": t.status} for t in result.traces],
    }

    lines = [f"Response: {result.response.text}"]
    if result.response.safety_notes:
        lines.append("Safety notes:")
        for note in result.response.safety_notes:
            lines.append(f"  - {note}")
    lines.append(f"Traces: {len(result.traces)} stages")
    for trace in result.traces:
        lines.append(f"  {trace.stage_name}: {trace.status}")
    return "\n".join(lines)


def _prepare_dataset(job: Job) -> str:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from dataset_prep import prepare_from_hf
    outputs = prepare_from_hf(ROOT / "dataset")
    lines = ["Dataset preparation complete:"]
    for name, path in outputs.items():
        lines.append(f"  {name}: {path}")
    return "\n".join(lines)


def _train_model(job: Job) -> str:
    data_path = ROOT / "dataset" / "emotion_train.jsonl"
    output_path = ROOT / "models" / "emotion_model.json"
    if not data_path.exists():
        raise FileNotFoundError(f"Training data not found at {data_path}. Run dataset preparation first.")
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    from pipeline.stages.emotion_engine.train_nlp_emotion_model import train_from_jsonl
    saved = train_from_jsonl(data_path, output_path)
    return f"Model saved to {saved}"


def _run_tests(job: Job) -> str:
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "tests", "-v"],
        capture_output=True, text=True, cwd=str(ROOT),
        env={**sys.environ, "PYTHONPATH": str(SRC_PATH)},
        timeout=120,
    )
    output = result.stdout + result.stderr
    passed = output.count(" ok")
    failed = output.count(" FAIL")
    errors = output.count(" ERROR")
    total = passed + failed + errors
    job.result_data = {
        "passed": passed, "failed": failed, "errors": errors, "total": total,
        "raw": output,
    }
    lines = [f"Tests: {passed}/{total} passed"]
    if failed:
        lines.append(f"  Failed: {failed}")
    if errors:
        lines.append(f"  Errors: {errors}")
    lines.append("")
    lines.append(output)
    return "\n".join(lines)


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
    return _job_to_dict(job)


@app.post("/api/dataset/prepare")
async def api_dataset_prepare():
    job = _spawn(_prepare_dataset)
    return _job_to_dict(job)


@app.post("/api/model/train")
async def api_model_train():
    job = _spawn(_train_model)
    return _job_to_dict(job)


@app.post("/api/tests/run")
async def api_tests_run():
    job = _spawn(_run_tests)
    return _job_to_dict(job)


@app.get("/api/health")
async def api_health():
    import urllib.request as _req
    checks = []

    config_path = ROOT / "configs" / "config.json"
    config = {}
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))

    provider = config.get("llm_provider", "ollama")
    model_name = config.get("model_name", "mistral")

    checks.append({"name": "Heuristic Emotion", "status": "ready", "detail": "Pure Python, no dependencies"})
    checks.append({"name": "NLP Emotion Model", "status": "ready", "detail": "SampleNLPEmotionModel, always available"})

    model_path = ROOT / "models" / "emotion_model.json"
    if model_path.exists():
        checks.append({"name": "Trained Emotion Model", "status": "ready", "detail": str(model_path)})
    else:
        checks.append({"name": "Trained Emotion Model", "status": "missing", "detail": "Not found. Run training first."})

    # Check Ollama
    ollama_url = config.get("ollama_base_url", "http://localhost:11434")
    ollama_ok = False
    try:
        r = _req.Request(f"{ollama_url}/api/tags", method="GET")
        with _req.urlopen(r, timeout=3) as resp:
            data = json.loads(resp.read())
            models = [m.get("name", "") for m in data.get("models", [])]
            if any(model_name in m for m in models):
                checks.append({"name": f"Ollama ({model_name})", "status": "ready", "detail": f"Endpoint: {ollama_url}"})
                ollama_ok = True
            else:
                checks.append({"name": f"Ollama ({model_name})", "status": "wrong_model", "detail": f"Available: {', '.join(models) or 'none'}"})
    except Exception:
        checks.append({"name": f"Ollama ({model_name})", "status": "offline", "detail": f"Cannot reach {ollama_url}"})

    # Check llama.cpp
    llamacpp_url = config.get("llamacpp_base_url", "http://localhost:8080")
    llamacpp_ok = False
    try:
        r = _req.Request(f"{llamacpp_url}/health", method="GET")
        with _req.urlopen(r, timeout=3) as resp:
            llamacpp_ok = resp.status == 200
            checks.append({"name": f"llama.cpp", "status": "ready", "detail": f"Endpoint: {llamacpp_url}"})
    except Exception:
        checks.append({"name": f"llama.cpp", "status": "offline", "detail": f"Cannot reach {llamacpp_url}"})

    ollama_reachable = ollama_ok or any(c["name"].startswith("Ollama") and c["status"] == "wrong_model" for c in checks)
    llamacpp_reachable = llamacpp_ok
    provider_reachable = ollama_reachable if provider == "ollama" else llamacpp_reachable

    rl_enabled = config.get("reasoning_loop_enabled", False)
    if not rl_enabled:
        checks.append({"name": "Reasoning Loop", "status": "disabled", "detail": "Set reasoning_loop_enabled=true"})
    elif provider_reachable and not ollama_ok and provider == "ollama":
        checks.append({"name": "Reasoning Loop", "status": "blocked", "detail": f"Ollama running but model '{model_name}' not installed. Change model_name in config.json."})
    elif provider_reachable:
        checks.append({"name": "Reasoning Loop", "status": "ready", "detail": f"Using {provider}"})
    else:
        checks.append({"name": "Reasoning Loop", "status": "blocked", "detail": f"Enabled but {provider} is offline"})

    return {"checks": checks}


@app.get("/api/jobs")
async def api_jobs_list():
    return {"jobs": [_job_to_dict(j) for j in _jobs.values()]}


@app.get("/api/jobs/{job_id}")
async def api_job_status(job_id: str):
    job = _jobs.get(job_id)
    if not job:
        return {"error": "job not found"}
    return _job_to_dict(job)


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
        "summary_path": str(ROOT / "Summary.md"),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
