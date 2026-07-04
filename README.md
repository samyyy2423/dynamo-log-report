# dynamo/log-report — Fixed Terminal-Bench 2 (Harbor) Task

This repo contains the repaired version of the `dynamo/log-report` task from the
Project Dynamo "Fix the Broken Terminal-Bench Task" exercise, plus the real
Harbor evidence that it now grades correctly.

## Layout

```
log-report/            The corrected task, in TB2/Harbor format
├── task.toml
├── instruction.md
├── environment/
│   ├── Dockerfile
│   └── access.log
├── solution/
│   ├── solve.sh
│   └── solve.py
└── tests/
    ├── test.sh
    └── test_outputs.py

evidence/               Real `harbor run` output (not simulated)
├── oracle/             reward.txt, ctrf.json, test-stdout.txt, result.json, produced-report.json
└── nop/                reward.txt, ctrf.json, test-stdout.txt, result.json

SUBMISSION.md           Full write-up: every corrected file, plus the analysis
                        of why the original verifier was broken
```

## Reproducing the evidence

With Docker and Harbor (`pip install harbor` / `uv tool install harbor`) available:

```bash
harbor run -p log-report -a oracle     # reference solution -> reward 1
harbor run -p log-report --agent nop   # no-op agent        -> reward 0
```

Results land in `jobs/<job-name>/<trial>/verifier/reward.txt` and `ctrf.json`,
matching the files committed under `evidence/`.

## What was broken, in short

The original task had five defects: a wrong/mistyped `artifacts` field in
`task.toml`, a leaked reference solution copied into the agent's Docker image,
an unpinned `:latest` base image, a verifier that only checked the output file
existed (not that its contents were correct), and a reward file written to a
path Harbor never reads. See [`SUBMISSION.md`](./SUBMISSION.md) for the full
breakdown, every corrected file in full, and the specific inputs that would
have passed the old verifier despite being wrong.
