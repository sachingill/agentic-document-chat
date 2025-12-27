### Local API Evaluation (Structured / Agentic / Multi-agent)

This repo includes a local evaluation runner that calls your running APIs and scores:
- **Answer quality**: correctness + completeness (LLM-judge, uses `expected_answer` if present)
- **Groundedness**: is the answer supported by retrieved context (LLM-judge verifier)
- **Retrieval quality**: context relevance + sufficiency (LLM-judge)
- **Safety**: input/output guardrails + API guardrail flags
- **Latency**: wall-clock per request
- **Cost**: best-effort (pattern relative-cost estimates when available)

#### 1) Start the unified API

Make sure `uvicorn app.main:app` is running on `127.0.0.1:8000`.

#### 2) Run the eval runner

```bash
python scripts/eval_local_api_runner.py \
  --base-url http://127.0.0.1:8000 \
  --dataset datasets/eval_cases_local_api.jsonl \
  --out eval_results/local_api_eval_results.jsonl \
  --max-concurrency 3
```

#### 3) Customize test cases

Edit `datasets/eval_cases_local_api.jsonl` and add rows like:

```json
{"id":"case_id","workflow":"structured|agentic|multiagent","pattern":"auto|sequential|parallel|supervisor","inference_mode":"low|balanced|high","question":"...","expected_answer":"..."}
```

Notes:
- `pattern` is only used for `workflow="multiagent"`.
- `expected_answer` is optional but recommended for quality scoring.


