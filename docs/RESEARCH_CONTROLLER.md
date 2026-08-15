# Research controller design

## Purpose

The research controller turns the existing one-pass loop into a measurable, bounded learning system. It selects the next peaceful-use research area from evidence in prior reports and the knowledge graph, records why a topic was selected, applies a stricter admission gate before minting, and turns developer analysis into reviewable proposals rather than autonomous production-code changes.

## Controller contract

| Capability | Behaviour | Safety boundary |
|---|---|---|
| Agenda selection | Scores categories by under-coverage, rejection history, recency and rotation; returns one transparent category recommendation per cycle. | Only approved civilian-energy categories are eligible. No prompt may bypass the existing safety guard. |
| Evidence gate | Combines independent evaluation samples, citation quality, novelty against existing knowledge and the existing fallback/provider checks. | A missing evaluator, fallback provider, weak citations or low agreement always rejects minting. |
| Decision record | Stores agenda reasoning, quality metrics, approval/rejection reasons and operational metadata in every report. | No secrets, raw provider keys or private configuration are stored. |
| Development proposals | Extracts non-executable improvement ideas from developer analysis and stores them in a durable proposal queue. | It never edits production code, changes safety policy, opens external accounts or makes financial/chain commitments. Any code change must be a reviewable pull request with passing checks. |
| Learning signal | Updates category coverage and quality history after each cycle, so future selection is informed by observed outcomes. | The controller changes topic priority only; it does not weaken thresholds autonomously. |

## Agenda score

For each eligible category, the controller calculates a deterministic priority score. Higher scores are selected first.

`priority = 0.45 × coverage_gap + 0.25 × rejection_signal + 0.20 × recency_gap + 0.10 × rotation_bonus`

Coverage gap rewards categories with fewer prior cycles. Rejection signal rewards categories whose prior work did not pass the quality gate, rather than repeating already-successful material. Recency gap avoids immediately revisiting a category. Rotation bonus prevents one category from dominating because of a short-term score fluctuation.

## Admission gate

The controller requires all of the following before a virtual-ledger record may be minted:

1. The answer came from a non-fallback research provider.
2. At least one real evaluator answered; multi-sample consistency must meet the configured threshold whenever multiple samples are requested.
3. Citation quality, novelty, accuracy, usefulness and composite readiness pass the strict published thresholds.
4. Existing nuclear-safety filtering permits the question and the final output.
5. The decision is persisted with explicit reasons, allowing any mint to be audited from the report alone.

## Proposal lifecycle

Developer analysis may yield a proposal with a title, rationale, impact area and evidence link. The controller writes proposals as `proposed`; it never applies them. A later quality workflow may classify proposals as documentation, test coverage, data curation or code work. Code work remains limited to a pull request with tests; safety-policy and financial/real-chain work always require a human decision.

## Compatibility

The controller is additive. A manual category hint continues to override automatic selection. Existing reports remain readable because new fields are optional. The current GitHub schedule remains the trigger, so no persistent service, browser session or hard-coded credential is introduced.
