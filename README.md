# Emotive Pipeline Baseline

This workspace contains a modular baseline for an emotive AI pipeline with one folder per stage.

## Structure
- DOCs/: project documentation
- src/pipeline/contracts/: shared data models and interfaces
- src/pipeline/stages/: isolated stage modules
- src/pipeline/orchestrator/: end-to-end pipeline wiring
- src/pipeline/config/: runtime config package

## Run
1. Ensure Python 3.10+ is available.
2. Run:

```bash
python -m pipeline.orchestrator.runner
```

## Notes
- The LLM client is currently a local stub.
- Replace src/pipeline/stages/llm_client/stage.py with a real Ollama implementation in the next iteration.
