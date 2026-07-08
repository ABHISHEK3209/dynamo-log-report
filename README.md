# log-report

A Terminal-Bench 2 (Harbor) task. The agent parses an Apache-style access log at
`/app/access.log` and writes a small JSON summary report to `/app/report.json`
with three fields: the total number of requests, the number of distinct client
IP addresses, and the single most-requested path.

## Layout

```
log-report/
  task.toml                 manifest (artifact, metadata, timeouts, environment)
  instruction.md            the prompt the agent receives
  environment/
    Dockerfile              single image, pinned base, bakes the test deps
    access.log              the input log
  solution/
    solve.sh                reference solution entry point
    solve.py               reference solution logic
  tests/
    test.sh                 runs pytest, writes reward + ctrf to /logs/verifier
    test_outputs.py         one test per success criterion
```

## Run it

From this directory:

```bash
harbor run -p log-report -a oracle     # reference solution, expect reward 1
harbor run -p log-report --agent nop   # no-op agent, expect reward 0
```

## How it is graded

After the agent stops, the verifier loads `/app/report.json` and checks four
things, one per numbered success criterion in `instruction.md`:

1. the file is a JSON object with exactly the keys total_requests, unique_ips, top_path
2. total_requests is the number of request lines in the log
3. unique_ips is the number of distinct client IPs
4. top_path is the most frequently requested path

The reward (1 or 0) and the CTRF report are written to `/logs/verifier/`.
