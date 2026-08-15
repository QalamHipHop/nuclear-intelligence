# Keyless GitHub → Hugging Face publishing

## Purpose

The project publishes only through short-lived GitHub OpenID Connect (OIDC) credentials. No Hugging Face access token is committed to the repository, written to workflow files, or stored as a GitHub Action secret.

## One-time Hugging Face configuration

A repository administrator must add the following **Trusted Publisher** entries in the target repositories' **Settings → Trusted Publishers** pages.

| Target | Provider | Required claims |
|---|---|---|
| `Qalam/Nuclear-Intelligence` Space | GitHub Actions | `repository = QalamHipHop/nuclear-intelligence`; `branch = main`; `workflow = deploy-hf.yml` |
| `Qalam/nuclear-intelligence-dataset` Dataset | GitHub Actions | `repository = QalamHipHop/nuclear-intelligence`; `branch = main`; `workflow = operation-loop.yml` |

The workflow files request `id-token: write`. The Hugging Face CLI then exchanges the GitHub identity for a repository-scoped token that expires after one hour.

## Deployment contract

1. GitHub is the canonical source of code.
2. Only `hf_deploy/` is mirrored to the Space. Runtime reports, local state, logs, `.env` files, and GitHub workflow files never enter the deployment bundle.
3. The Space deployment workflow fails if OIDC cannot be exchanged or the curated deployment bundle is incomplete.
4. Research publication to the public dataset is explicit. With `REQUIRE_HF_SYNC=true`, a failed dataset publication marks the automation run as failed rather than reporting a misleading success.
5. Long-lived LLM-provider credentials, if any are needed for runtime inference, belong only in Hugging Face Space secrets or GitHub Action secrets. They are not part of OIDC publishing and must never be echoed in logs.

## Rotation and incident response

OIDC publishing credentials expire automatically. If a trusted publisher needs to be revoked, remove it from the corresponding Hugging Face repository settings; no code change or secret rotation is required. Review the GitHub Actions run log and the Hugging Face repository commit history when investigating a deployment incident.

## References

- [Hugging Face Trusted Publishers](https://huggingface.co/docs/hub/en/trusted-publishers)
- [Hugging Face GitHub Actions integration](https://huggingface.co/docs/hub/en/repositories-github-actions)
- [Managing Spaces with GitHub Actions](https://huggingface.co/docs/hub/en/spaces-github-actions)
