# Dynamo — Fix the Broken Terminal-Bench Task (log-report)

Corrected task: [`log-report/`](./log-report). Real Harbor evidence: [`evidence/`](./evidence)
(`oracle` → reward 1, ctrf 4/4 passed; `nop` → reward 0, ctrf 0/4 passed).

Verified with real `harbor run` on Docker Engine (Terminal-Bench 2 / Harbor 0.17.1):

```
harbor run -p log-report -a oracle     # reward 1  (ctrf: 4 passed / 0 failed)
harbor run -p log-report --agent nop   # reward 0  (ctrf: 0 passed / 4 failed)
```

---

## Corrected `task.toml`

```toml
artifacts = ["/app/report.json"]

[task]
name = "dynamo/log-report"
description = "Parse an Apache-style access log into a small JSON summary report."

[metadata]
category = "data_processing_and_etl"
subcategory = "text_processing"
task_objective = ["transform", "generate"]
artifact_type = ["text_or_log_file", "generated_output_artifact"]
expert_time_estimate_hours = 0.3
model_tested = "GPT-5.4"
agent_tested = "Terminus-2"
difficulty_explanation = "Parse a small access log and emit summary stats."
solution_explanation = "Read the log, count requests/unique IPs, find the top path."
verification_explanation = "Assert the exact report values (counts and top path), not just that a file exists."

[verifier]
timeout_sec = 120.0

[agent]
timeout_sec = 120.0

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 2048
storage_mb = 10240
gpus = 0
allow_internet = true
mcp_servers = []
```

**Fixes vs. the broken original**

- `artifacts` was `"/app/out.json"` — a **string**, and pointing at a file the task never
  produces. Now a **top-level TOML array** `["/app/report.json"]` matching the real output.
- `verification_explanation` updated to describe real value-checking (the old verifier only
  checked existence).
- `[task]`, `[metadata]` (all template fields), `[verifier]`, `[agent]`, `[environment]`
  present. No `avg_at_8`, `tags`, or `schema_version`.

---

## Corrected `environment/Dockerfile`

```dockerfile
FROM python:3.13-slim-bookworm@sha256:fcbd8dfc2605ba7c2eca646846c5e892b2931e41f6227985154a596f26ab8ed7

RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

WORKDIR /app

COPY access.log /app/access.log
```

**File removed from the build context:** `environment/solution_hint.py` — a full copy of the
reference solution (its own header read *"Reference implementation (leaked into the agent
image by mistake)"*). It was deleted **and** its `COPY solution_hint.py /app/solution_hint.py`
line was removed, so the agent image no longer contains the answer.

**Other fixes**

- Base image was `python:latest` (never allowed). Now an approved base
  (`python:3.13-slim-bookworm`) **pinned by `@sha256` digest** for reproducibility.
- `pytest` + `pytest-json-ctrf` are baked in and pinned, so `test.sh` installs nothing at
  verify time.
- No network needed at runtime (build-time `pip` only).

---

## Why is the original verifier bad?

The original `tests/test_outputs.py` only checked:

```python
def test_report_exists():
    assert Path("/app/report.json").exists()

def test_report_nonempty():
    assert Path("/app/report.json").stat().st_size > 0
```

and `test.sh` wrote the reward to `/app/reward.txt`.

It is broken in two independent ways:

1. **It grades existence, not correctness — wrong answers pass.** Anything non-empty at
   `/app/report.json` scores reward 1. All of these would PASS the original verifier even
   though every one is wrong:
   - `echo hello > /app/report.json` (not even JSON)
   - `echo '{}' > /app/report.json` (valid JSON, none of the required fields)
   - `echo '{"total_requests": 999, "unique_ips": 999, "top_path": "/nope"}'` (valid shape,
     wrong values)

   So an agent that fabricates a report, or emits the right shape with garbage numbers, is
   graded identical to the true solution. There is no check of `total_requests`, `unique_ips`,
   or `top_path`, so the verifier cannot distinguish a correct solution from a plausible-looking
   wrong one — the classic misaligned-verifier failure.

2. **The reward is written to the wrong place, so Harbor never reads it.** Harbor reads
   `/logs/verifier/reward.txt`; the original wrote `/app/reward.txt`. Under a real
   `harbor run` this raises `RewardFileNotFoundError` — even the reference/oracle solution
   cannot score. No `ctrf.json` was produced either.

The corrected verifier asserts the actual values (one test per numbered instruction criterion)
and writes `reward.txt` **and** `ctrf.json` to `/logs/verifier/`.

---

## Corrected verifier

### `tests/test_outputs.py`

```python
import json
from pathlib import Path

import pytest

REPORT = Path("/app/report.json")


@pytest.fixture(scope="module")
def report():
    """Load the report; failure here means criterion 1 is unmet."""
    assert REPORT.exists(), "no report.json at /app/report.json"
    with REPORT.open() as f:
        data = json.load(f)
    assert isinstance(data, dict), "report.json must be a single JSON object"
    return data


def test_report_is_json_object():
    """Criterion 1: /app/report.json exists and contains a single JSON object."""
    assert REPORT.exists(), "no report.json at /app/report.json"
    with REPORT.open() as f:
        data = json.load(f)
    assert isinstance(data, dict), "report.json must be a single JSON object"


def test_total_requests(report):
    """Criterion 2: total_requests equals the number of request lines (6)."""
    assert report["total_requests"] == 6


def test_unique_ips(report):
    """Criterion 3: unique_ips equals the count of distinct client IPs (3)."""
    assert report["unique_ips"] == 3


def test_top_path(report):
    """Criterion 4: top_path is the most frequently requested path (/index.html)."""
    assert report["top_path"] == "/index.html"
```

Four tests, one per numbered success criterion in `instruction.md`, each docstring naming the
criterion it verifies. No criterion left unchecked; no test for anything the instruction does
not state. Expected values are derived from the shipped `access.log` (6 request lines; IPs
`192.168.0.1`, `192.168.0.2`, `10.0.0.5`; `/index.html` ×3 vs `/about.html` ×2, `/api/login` ×1).

### `tests/test.sh`

```bash
#!/bin/bash

# pytest + pytest-json-ctrf are baked into the environment image
# (environment/Dockerfile), so this installs nothing at verify time.
mkdir -p /logs/verifier
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
code=$?

if [ $code -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

Plain `pytest` (no `uvx`/`pip`/`curl` at verify time), writing both `reward.txt` and
`ctrf.json` to `/logs/verifier/`.

---

## Rewritten `instruction.md`

```
There is an Apache-style access log at /app/access.log. Analyse the traffic and
write a summary report, as a single JSON object, to the file /app/report.json.
Use these exact key names: total_requests, unique_ips, top_path. Write only the
JSON object to that file, with no extra text.

Your report is correct when it meets all of the following criteria:

1. /app/report.json exists and contains a single JSON object.
2. total_requests equals the total number of request lines in /app/access.log.
3. unique_ips equals the number of distinct client IP addresses in the log,
   taking the first whitespace-separated field of each line as the client IP.
4. top_path equals the request path that appears in the greatest number of
   requests.
```

Prompt style (no title, no `##` headers), states the exact absolute output path and format,
gives four numbered unambiguous criteria that map 1:1 to the verifier, leaks no solution, and
is well under 1500 tokens.

---

## Four-way consistency

The output path is identical across all four places:

| Where | Value |
|---|---|
| `instruction.md` | `/app/report.json` |
| `task.toml` `artifacts` | `["/app/report.json"]` |
| `tests/test_outputs.py` | `/app/report.json` |
| `solution/solve.py` (what `solve.sh` writes) | `/app/report.json` |
