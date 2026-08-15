# Shared-runtime migration plan

## Objective

The GitHub automation, API, and Hugging Face Space must execute one canonical research runtime. The Space must be a presentation layer, rather than a second implementation of research, safety, evaluation, ledger, or autonomous-loop logic.

## Target contract

| Layer | Responsibility | Source of truth |
|---|---|---|
| `core/` and `blockchain/` | Research, safety filtering, evaluator gates, knowledge graph, ledger, runtime configuration and research controller | Repository root |
| `core_hf.py` | Import-safe adapter that exposes only public, safe actions for the Space | Repository root |
| `hf_deploy/space_app.py` | Gradio presentation layer: overview, research, evidence, governance and ledger views | Repository root |
| `.github/workflows/deploy-hf.yml` | Curates a build context containing the canonical runtime and thin Space UI | Repository root |
| Hugging Face Space | Executes the curated build context only | Generated from an approved GitHub commit |

## Migration design

The deploy workflow will construct a temporary Space build context. It will copy the root `requirements.txt`, canonical `core/`, `blockchain/`, supporting `scripts/`, `core_hf.py`, and the thin `space_app.py`. A Dockerfile within the curated bundle copies that build context and starts only the presentation entrypoint.

The old `hf_deploy/app.py` remains during the transition as a historical fallback source, but it is no longer selected by the deployment workflow. The deployment verification checks that the thin UI imports the canonical adapter and that no local research engine class is defined inside the Space entrypoint.

## Compatibility and safety

The adapter will preserve manual Q&A, cycle execution, report export, knowledge search and ledger status. It will call the canonical query and answer safety filters before returning any material to the UI. Governance data is read from the same operation-loop history as GitHub Actions; no browser token, LLM secret or Hugging Face publishing credential is exposed through the UI.

## Product surface after migration

The Space will expose a concise professional interface: operational overview, guided research, evidence and source review, governance decision log and development-proposal queue, knowledge retrieval, and ledger integrity. User-triggered work is serialized so concurrent research cycles do not overlap.

## Acceptance criteria

1. The Space build includes the canonical runtime, not a duplicated research core.
2. A static deployment test rejects a Space entrypoint that redefines the research engine.
3. The adapter and Space UI are importable headlessly.
4. Existing safety tests, controller tests, and health checks pass.
5. The deployed Space reaches `RUNNING`; its public endpoint responds after the bundle is published.
