# Product-growth audit — Nuclear Intelligence

## Evidence-based current state

The project already has a one-pass autonomous research loop: it generates a question, writes an answer, evaluates it, integrates approved knowledge, and optionally records a virtual-ledger event. GitHub Actions run this loop every 25 minutes, while the Hugging Face Space supplies a user interface.

The meaningful safety controls are present: sensitive nuclear requests are filtered before model execution, output filtering exists, and fallback/demo providers are prevented from minting. The deployment package includes equivalent protections for Persian high-risk requests.

## Confirmed gaps

| Gap | Evidence | Product risk | Recommended direction |
|---|---|---|---|
| Research is a linear executor, not a learning controller | `OperationLoop` has no agenda, backlog, trend analysis, adaptive category selection, or follow-up planning | Repetitive research and weak evidence of self-improvement | Add a durable research agenda that scores underexplored categories, tracks outcomes, and selects the next question deterministically. |
| Stronger evaluation exists but is not in the main minting path | `core/evaluation_enhanced.py` provides citation quality, multi-sample consistency, novelty comparison, and a strict readiness gate | A single evaluator result can still dominate a high-value decision | Integrate the enhanced readiness gate into the operation loop; record decisions and reasons in every report. |
| Dataset publication is currently blocked | The 2026-08-15 research workflow failed because the Hugging Face Dataset has no matching Trusted Publisher | A successful research cycle can be reported while public synchronization remains incomplete | Add the same limited, secret-backed compatibility route used for Space deployment, while retaining OIDC as the preferred future path. |
| Repository commits routine runtime output | The scheduled workflow commits reports, ledger state, and logs every cycle | Repository growth, noisy history, and conflict risk | Publish immutable reports to the dataset and retain compact operational summaries in Git; keep the ledger as a verified snapshot. |
| No product-level research governance loop | Developer analysis is saved but does not influence the next cycle | "Self-development" remains an aspiration rather than a measurable system | Add a proposal queue with an approval policy: safe low-risk documentation/tests may be proposed automatically; code changes require a pull request and passing checks. |

## Boundaries

The system must not autonomously modify production code, change safety policies, create external financial commitments, or issue real blockchain transactions without a reviewable pull request and quality gates. It may autonomously gather, score, publish, and propose peaceful-use research within the configured policy.
