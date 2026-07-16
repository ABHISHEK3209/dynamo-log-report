# Assessment 1 - Dynamo: Fix the Broken Terminal-Bench Task

Repair a broken Terminal-Bench 2 (Harbor) task, then submit the fix. The underlying
task is simple software engineering (parse an access log into a small JSON report);
the assessment is about spotting bad task authoring and repairing it into correct
Harbor format.

Repo (fixed task): https://github.com/ABHISHEK3209/dynamo-log-report

---

## Step 1 - Diagnose (which defects are present)

Selected (real defects):

1. task.toml: artifacts is a string instead of an array (and points to the wrong file)
2. environment/Dockerfile uses an unpinned base image
3. the agent image leaks the reference solution (solution_hint.py COPYed in)
4. the verifier is gameable (checks the file exists, not its values)
5. tests/test.sh writes reward to the wrong path and/or omits ctrf.json
6. instruction.md is ambiguous and inconsistent with the verifier

Not selected (not real defects):

- the access.log input file is corrupted
- the task requires network access at runtime to be solved
- the solution/solve.sh oracle computes the wrong answer
- the memory_mb limit is too low to run the verifier

---

## Step 2 - Fixes

### Corrected task.toml

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
difficulty_explanation = "Parse a small Apache-style access log and emit summary stats: total requests, unique client IPs, and the single most-requested path."
solution_explanation = "Read /app/access.log line by line, count non-empty lines as requests, collect the first field of each line as the client IP into a set, extract the path from the HTTP request line with a regex, then report total_requests, unique_ips, and the most common path."
verification_explanation = "Load /app/report.json and assert it is a JSON object with exactly the keys total_requests, unique_ips, top_path, and that total_requests == 6, unique_ips == 3, top_path == '/index.html' for the shipped log."

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

### Corrected environment/Dockerfile

Also delete environment/solution_hint.py from the build context (the leaked solution).

```dockerfile
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

WORKDIR /app

COPY access.log /app/access.log
```

### Why is the original verifier bad?

The original tests/test_outputs.py only checks that /app/report.json EXISTS and is
NON-EMPTY. It never reads the contents, so any file with at least one byte passes
with reward 1. All of these would wrongly PASS despite not doing the task:

- echo hi > /app/report.json
- writing {} (an empty JSON object)
- cp /app/access.log /app/report.json  (the raw log copied verbatim)
- a wrong summary, e.g. {"total_requests": 999, "unique_ips": 0, "top_path": "/nope"}

It verifies none of the three required values (total_requests, unique_ips, top_path),
so a wrong-but-present file scores the same as the correct one. Separately,
tests/test.sh wrote the reward to /app/reward.txt (Harbor reads
/logs/verifier/reward.txt) and never produced ctrf.json, so even a correct run was
misreported as a silent failure.

### Corrected verifier - tests/test_outputs.py

```python
import json
from pathlib import Path

REPORT = Path("/app/report.json")
REQUIRED_KEYS = {"total_requests", "unique_ips", "top_path"}


def load_report():
    return json.loads(REPORT.read_text())


def test_report_schema():
    """Criterion 1: /app/report.json exists and is a JSON object whose keys are
    exactly total_requests, unique_ips, and top_path."""
    assert REPORT.exists(), "no report.json found"
    data = load_report()
    assert isinstance(data, dict), "report.json must be a JSON object"
    assert set(data.keys()) == REQUIRED_KEYS, f"unexpected keys: {sorted(data.keys())}"


def test_total_requests():
    """Criterion 2: total_requests equals the number of non-empty request lines
    in /app/access.log (6)."""
    data = load_report()
    assert data["total_requests"] == 6


def test_unique_ips():
    """Criterion 3: unique_ips equals the number of distinct client IPs
    in /app/access.log (3)."""
    data = load_report()
    assert data["unique_ips"] == 3


def test_top_path():
    """Criterion 4: top_path equals the most frequently requested path
    in /app/access.log (/index.html)."""
    data = load_report()
    assert data["top_path"] == "/index.html"
```

### Corrected verifier - tests/test.sh

```bash
#!/bin/bash
# pytest and pytest-json-ctrf are baked into the single environment image
# (environment/Dockerfile) - nothing is installed at verify time. Always exit 0;
# the pass/fail signal lives in /logs/verifier/reward.txt.
mkdir -p /logs/verifier

pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA

if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
```

### Rewritten instruction.md

```text
Parse the Apache-style access log at /app/access.log and write a JSON summary
report to /app/report.json.

Each non-empty line of the log is one request. A line begins with the client IP
address (the first whitespace-separated field) and contains an HTTP request line
of the form "METHOD PATH PROTOCOL", for example "GET /index.html HTTP/1.1".

Write /app/report.json as a single JSON object with exactly these three keys:

- "total_requests": integer, the number of non-empty request lines in the log.
- "unique_ips": integer, the number of distinct client IP addresses.
- "top_path": string, the request PATH that appears most often across all requests.

Success criteria:

1. /app/report.json exists and is a JSON object whose keys are exactly
   "total_requests", "unique_ips", and "top_path".
2. "total_requests" equals the number of non-empty request lines in /app/access.log.
3. "unique_ips" equals the number of distinct client IP addresses in /app/access.log.
4. "top_path" equals the most frequently requested path in /app/access.log.

Do not modify /app/access.log.

You have 120 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
```

---

## Step 3 - Evidence & submission

### Summarize what was broken and why (four axes)

Format (task.toml): artifacts was a quoted string, "/app/out.json", instead of a
TOML array, and it named a file the task never creates. Harbor expects artifacts to
be a top-level array of the output paths the verifier reads, so this was both the
wrong type and pointed at the wrong file. Fixed to artifacts = ["/app/report.json"],
which is what the solution actually writes.

Environment (environment/Dockerfile): the base image was python:latest, an unpinned
floating tag, so the build is not reproducible - a later rebuild can pull a different
python. It also COPYed solution_hint.py, a full copy of the reference solution, into
the agent image, leaking the answer to the agent. Fixed by pinning an approved base
image by sha256 digest and removing the leaked file from the build context (only
access.log is copied now).

Verifier (tests/): the tests only checked that /app/report.json existed and was
non-empty, never reading the values, so any non-empty file passed - a wrong report,
an empty object, or even the raw log copied over. Also, test.sh wrote the reward to
/app/reward.txt (Harbor reads /logs/verifier/reward.txt) and never produced
ctrf.json, so a correct run was misreported. Fixed with four tests that assert the
real values, and a test.sh that writes reward.txt and ctrf.json to /logs/verifier.

Instruction (instruction.md): the prompt was vague - "save your findings so they can
be reviewed" - with no output path, file name, format, or field names, so it did not
match what the verifier checks. Rewritten to name the exact output file, the exact
JSON keys and their meaning, and four numbered success criteria that map one-to-one
to the four tests.

### Passing verifier output from the fixed task (both runs)

```text
=== harbor run -p log-report -a oracle ===
reward.txt: 1

ctrf summary:
{"tests": 4, "passed": 4, "failed": 0, "skipped": 0, "pending": 0, "other": 0}
  test_outputs.py::test_report_schema    passed
  test_outputs.py::test_total_requests   passed
  test_outputs.py::test_unique_ips       passed
  test_outputs.py::test_top_path         passed

=== harbor run -p log-report --agent nop ===
reward.txt: 0

ctrf summary:
{"tests": 4, "passed": 0, "failed": 4, "skipped": 0, "pending": 0, "other": 0}
  test_outputs.py::test_report_schema    failed
  test_outputs.py::test_total_requests   failed
  test_outputs.py::test_unique_ips       failed
  test_outputs.py::test_top_path         failed
```

### Prove the verifier catches a wrong solution

Bugged solution/solve.sh (writes total_requests = 999 instead of the real 6):

```bash
#!/bin/bash
set -euo pipefail

python3 /solution/solve.py

# BUG: clobber total_requests with a wrong value (should be 6).
python3 - <<'PY'
import json
p = "/app/report.json"
d = json.load(open(p))
d["total_requests"] = 999
json.dump(d, open(p, "w"))
PY
```

Verifier output with the bug in place:

```text
=== harbor run -p log-report -a oracle (bugged) ===
Reward: 0.0
reward.txt: 0

ctrf summary:
{"tests": 4, "passed": 3, "failed": 1, "skipped": 0, "pending": 0, "other": 0}
  test_outputs.py::test_report_schema    passed
  test_outputs.py::test_total_requests   failed
  test_outputs.py::test_unique_ips       passed
  test_outputs.py::test_top_path         passed
```

The wrong count fails test_total_requests, so the reward drops to 0. The verifier
rejects an incorrect solution instead of passing it. The correct solve.sh was then
restored.

### Link to full fixed task

https://github.com/ABHISHEK3209/dynamo-log-report

(Make the repo private after passing the assessment.)
