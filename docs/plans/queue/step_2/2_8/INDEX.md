# 2.8: Implement OllamaJob

## Atomic Steps
1. Read `OllamaExecutor` body
2. Create `ai_admin/jobs/ollama_job.py` with `class OllamaJob(QueueJobBase)`
3. Implement `run()`: dispatch by `params["operation"]` → pull/run
4. Port Ollama API calls (model_name, prompt, max_tokens, temperature)
5. For `run` operation: stream tokens and report progress incrementally
6. Handle model-not-found error gracefully
7. Docstring, type hints, lint + typecheck
