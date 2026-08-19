# Public Access and Security

The Hugging Face Space is public for **read-only status, governance, ledger verification, knowledge search and manual civilian-energy research**. Public access does not expose credentials, filesystem paths, operator diagnostics, development prompts or durable write operations.

## Public controls

The following environment variables are intentionally conservative by default:

| Variable | Default | Purpose |
|---|---:|---|
| `PUBLIC_MAX_QUERY_CHARS` | `2000` | Maximum length for public research and search input; bounded to 100–4000. |
| `PUBLIC_RATE_LIMIT_PER_MINUTE` | `20` | In-process sliding-window limit for public callbacks; bounded to 1–120. |
| `PUBLIC_CYCLE_ENABLED` | `false` | Keeps autonomous durable research cycles disabled for anonymous visitors. |
| `PUBLIC_DATASET_WRITE_ENABLED` | `false` | Keeps public-triggered Dataset publication disabled. |

The public interface always disables development-mode analysis. Any autonomous cycle or Dataset publication should run through the reviewed GitHub Actions workflow with operator-managed credentials and trusted-publisher permissions.

## Credential policy

Secrets such as `HF_TOKEN`, provider API keys and GitHub credentials must be supplied through the Hugging Face Space secret store or GitHub Actions secrets. They must never be committed, included in a URL, passed as a command-line argument, printed in diagnostics or returned by a public status endpoint.

The service returns generic public error messages and keeps detailed exceptions in operator logs. Public status deliberately omits absolute filesystem paths and initialization exception text.

## Accuracy and safety boundary

All manual questions pass through the canonical safety guard, the shared research runtime and answer validation. Public research is evidence-led and does not guarantee correctness; users should inspect returned sources and quality signals. Requests involving weapon design, radiological dispersal, covert enrichment or other harmful operational assistance are refused. The public UI is intended for peaceful civilian-energy research, education and governance.

## Deployment checklist

Before enabling any write or autonomous capability, install the pinned dependencies, run `python3 -m compileall -q core scripts api tests`, run the complete unittest suite, verify the ledger, inspect GitHub Actions logs, and confirm that the Hugging Face Space and Dataset Trusted Publishers are configured. Keep `PUBLIC_CYCLE_ENABLED=false` and `PUBLIC_DATASET_WRITE_ENABLED=false` unless an operator has reviewed the threat model and rate-limit capacity.

## Autonomous operation

The scheduled research loop is a bounded one-cycle-per-run process. It is protected by `AUTONOMY_ENABLED`, `EMERGENCY_STOP`, a single-run lock and an audit record at `knowledge_base/autonomy_control.json`. Setting `EMERGENCY_STOP=true` stops the next run with a non-success exit code and records the reason without deleting evidence.

The autonomous developer is proposal-first. It periodically creates `reports/developer_queue.md` and opens a reviewable pull request containing the queue when it changes. It does not edit production code, merge pull requests, alter safety rules, access provider credentials, or publish external data. A human review and passing CI are required before implementation is merged.

| Capability | Automatic | Human approval required |
|---|---:|---:|
| Select a peaceful research topic | Yes | No |
| Run one governed research cycle | Yes, on schedule | No, while enabled |
| Record evidence and audit metadata | Yes | No |
| Generate developer proposals and queue | Yes | No |
| Change production code | No | Yes, through pull request |
| Change safety policy or thresholds | No | Yes |
| Merge or publish a code change | No | Yes |
| Use external credentials or make real-world commitments | No | Yes and scoped secrets |

## Fully automated production mode

The default production profile now enables autonomous operation, automatic developer-queue generation and Hugging Face synchronization. Each scheduler invocation remains bounded to one governed cycle, records an audit event and produces a reviewable developer queue. The system may continue operating without a browser session or manual prompting.

Automatic operation includes research selection, source gathering, evaluation, ledger admission, report persistence, Dataset synchronization, health checks and developer-queue refresh. It does not include unrestricted arbitrary code execution, safety-policy changes, secret creation, uncontrolled external transactions or irreversible merges. Those boundaries are technical safeguards, not a disabled mode.

For emergency shutdown, set `EMERGENCY_STOP=true` in the scheduler or deployment environment. For recovery, clear the flag only after inspecting the latest workflow log, report, ledger validity and `knowledge_base/autonomy_control.json`. The last known good Git commit remains the rollback point; do not delete reports or ledger evidence during recovery.
