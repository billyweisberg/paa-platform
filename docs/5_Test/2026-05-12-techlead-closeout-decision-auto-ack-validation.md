# 2026-05-12 TechLead Closeout Decision Auto-Ack Validation

## Goal

Validate that a self-addressed terminal `techlead_decision_packet` emitted by `techlead-closeout-qa-pass --send-decision` is automatically acknowledged after persistence and send, instead of being left behind on `fractal-core-architecture`.

## Setup

- consumer repo:
  - `<consumer_repo_root>`
- live closed pilot slice:
  - issue `108`
  - PR `109`
- passing QA packet still present on disk:
  - `<consumer_repo_root>/.project/data/paa/reports/qa-verification.issue108.qa.json`

## Command

```bash
cd <consumer_repo_root>
PYTHONPATH="$PWD/.codex/paa/vendor:$PWD/.codex/paa/lib" ./.venv/bin/python -m paa_consumer techlead-closeout-qa-pass \
  --repo-root <consumer_repo_root> \
  --package-id-external fcore-stagew7-2026-05-10-issue108-team-worker-automation-runtime-note \
  --brief-id-external fcore-coder-2026-05-10-issue108-team-worker-automation-runtime-note \
  --issue-number 108 \
  --send-decision
```

## Result

- command returned `ok: true`
- closeout decision compiled and sent:
  - `message_id = fcore-techlead-2026-05-12-issue108-close_slice`
- `decision_ack` returned success:
  - `claim_id = 5907cd5b-befe-49b5-b779-6c473a64ba0c`
  - `status = done`
- post-run queue state:
  - `fractal-core-architecture.messages_ready = 0`

## Conclusion

The correct policy for self-addressed terminal closeout decision packets is now implemented in runtime behavior:

- compile and persist the decision packet
- send it to `fractal-core-architecture`
- immediately claim and acknowledge it when it becomes the queue head

This removes meaningless residual closeout packets from the architecture queue while preserving durable decision artifacts on disk and in the DB.
