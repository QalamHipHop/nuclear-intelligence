#!/usr/bin/env python3
"""
Nuclear Intelligence v5.0 - Sync to HuggingFace Dataset & GitHub
═══════════════════════════════════════════════════════════════════
Uploads the latest cycle reports and knowledge base to:
- HuggingFace Dataset (Qalam/nuclear-intelligence-dataset) — public, no auth
- GitHub repository reports/ folder — via PyGithub
═══════════════════════════════════════════════════════════════════
"""
import os
import sys
import json
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.runtime_config import read_secret, validate_secret

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO", colorize=True,
           format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>")


def sync_hf_dataset(limit: int = 25) -> int:
    """Upload reports to HF only when explicitly enabled."""
    if os.getenv("SYNC_TO_HF", "false").strip().lower() not in {"1", "true", "yes", "on"}:
        logger.info("HF sync disabled; GitHub remains the primary persistence target")
        return 0
    try:
        from huggingface_hub import HfApi, create_repo
    except ImportError:
        message = "huggingface_hub not installed"
        if os.getenv("REQUIRE_HF_SYNC", "false").lower() == "true":
            logger.error(message)
            return 1
        logger.warning(f"{message} — skipping")
        return 0

    hf_status = validate_secret("HF_TOKEN", prefix="hf_")
    hf_token = read_secret("HF_TOKEN")
    if not hf_status.usable:
        message = "HF_TOKEN is not configured with a valid environment-backed shape"
        if os.getenv("REQUIRE_HF_SYNC", "false").lower() == "true":
            logger.error(message)
            return 1
        logger.warning(f"{message} — skipping HF sync")
        return 0

    try:
        api = HfApi(token=hf_token)
        try:
            user = api.whoami()
            logger.info(f"Authenticated to HF as: {user.get('name', 'unknown')}")
        except Exception as e:
            logger.warning("HF auth check failed; token was rejected or lacks access")

        dataset_repo = os.getenv("HF_DATASET_REPO", "Qalam/nuclear-intelligence-dataset")
        try:
            create_repo(
                repo_id=dataset_repo,
                repo_type="dataset",
                token=hf_token,
                exist_ok=True,
                private=False,
            )
            logger.success(f"Dataset ready: https://huggingface.co/datasets/{dataset_repo}")
        except Exception as e:
            logger.warning(f"Dataset ensure: {e}")

        reports_dir = Path(__file__).parent.parent / "reports"
        kb_dir = Path(__file__).parent.parent / "knowledge_base"

        if reports_dir.exists():
            report_files = sorted(reports_dir.glob("cycle_*.json"), key=lambda p: p.stat().st_mtime)[-limit:]
            uploaded = 0
            failures = 0
            for report_file in report_files:
                try:
                    api.upload_file(
                        path_or_fileobj=str(report_file),
                        path_in_repo=f"reports/{report_file.name}",
                        repo_id=dataset_repo,
                        repo_type="dataset",
                        commit_message=f"Auto: {report_file.name}",
                    )
                    uploaded += 1
                except Exception as e:
                    failures += 1
                    logger.warning(f"Failed to upload {report_file.name}: {e}")
            logger.info(f"📤 Uploaded {uploaded}/{len(report_files)} cycle reports")
            if report_files and uploaded == 0 and os.getenv("REQUIRE_HF_SYNC", "false").lower() == "true":
                logger.error(f"All {failures} report uploads failed")
                return 1

        for kb_file in ["knowledge_graph.json", "virtual_ledger.json", "nuclear_knowledge_base.json"]:
            kb_path = kb_dir / kb_file
            if kb_path.exists():
                try:
                    api.upload_file(
                        path_or_fileobj=str(kb_path),
                        path_in_repo=f"knowledge_base/{kb_file}",
                        repo_id=dataset_repo,
                        repo_type="dataset",
                        commit_message=f"Auto: update {kb_file}",
                    )
                except Exception as e:
                    logger.warning(f"Failed to upload {kb_file}: {e}")

        queue_path = kb_dir / "developer_queue.md"
        if queue_path.exists():
            try:
                api.upload_file(
                    path_or_fileobj=str(queue_path),
                    path_in_repo="knowledge_base/developer_queue.md",
                    repo_id=dataset_repo,
                    repo_type="dataset",
                    commit_message="Auto: update developer queue",
                )
                logger.info("Uploaded autonomous developer queue")
            except Exception as e:
                logger.warning(f"Failed to upload developer queue: {e}")

        # Update README with latest stats
        try:
            ledger_path = kb_dir / "virtual_ledger.json"
            kg_path = kb_dir / "knowledge_graph.json"
            nes_supply = 0
            chain_length = 0
            if ledger_path.exists():
                with open(ledger_path) as f:
                    d = json.load(f)
                    nes_supply = d.get("nes_supply", 0)
                    chain_length = len(d.get("chain", []))
            kg_entities = 0
            if kg_path.exists():
                with open(kg_path) as f:
                    d = json.load(f)
                    kg_entities = len(d.get("entities", {}))

            readme = f"""---
license: mit
task_categories:
  - question-answering
  - text-generation
tags:
  - nuclear
  - energy
  - research
  - blockchain
  - ai
size_categories:
  - n<1K
---

# Nuclear Intelligence Dataset

Public, auto-generated dataset of validated nuclear-energy research cycles.

**Latest stats (auto-updated):**
- 🪙 NES tokens minted: **{nes_supply:,.0f}**
- ⛓️ Blockchain length: **{chain_length}** blocks
- 🕸️ Knowledge entities: **{kg_entities}**

## Source
- GitHub: https://github.com/QalamHipHop/nuclear-intelligence
- HF Space: https://huggingface.co/spaces/Qalam/Nuclear-Intelligence

## License
MIT
"""
            api.upload_file(
                path_or_fileobj=readme.encode(),
                path_in_repo="README.md",
                repo_id=dataset_repo,
                repo_type="dataset",
                commit_message="Auto: update stats",
            )
        except Exception as e:
            logger.debug(f"README update skipped: {e}")

        return 0
    except Exception as e:
        logger.error("HF dataset sync error; inspect credential scope and repository access")
        return 1


def sync_github(limit: int = 10) -> int:
    """Optional API sync; workflow persistence uses a native git commit."""
    if os.getenv("SYNC_TO_GITHUB", "true").strip().lower() not in {"1", "true", "yes", "on"}:
        logger.info("GitHub API sync disabled; native workflow commit remains active")
        return 0
    try:
        from github import Github
    except ImportError:
        logger.warning("PyGithub not installed — skipping GH sync")
        return 0

    gh_status = validate_secret("GITHUB_TOKEN")
    token = read_secret("GITHUB_TOKEN")
    if not gh_status.usable:
        message = "GITHUB_TOKEN is not configured in the environment"
        if os.getenv("REQUIRE_GH_SYNC", "false").lower() == "true":
            logger.error(message)
            return 1
        logger.warning(f"{message} — skipping GH sync")
        return 0

    try:
        g = Github(token)
        repo_name = os.getenv("GH_REPO", "QalamHipHop/nuclear-intelligence")
        repo = g.get_repo(repo_name)
        logger.info(f"Connected to GH repo: {repo.full_name}")

        reports_dir = Path(__file__).parent.parent / "reports"
        kb_dir = Path(__file__).parent.parent / "knowledge_base"

        if reports_dir.exists():
            files = sorted(reports_dir.glob("cycle_*.json"), key=lambda p: p.stat().st_mtime)[-limit:]
            for f in files:
                try:
                    content = f.read_text(encoding="utf-8")
                    path = f"reports/{f.name}"
                    try:
                        existing = repo.get_contents(path)
                        repo.update_file(path, f"Auto: update {f.name}", content, existing.sha)
                    except Exception:
                        repo.create_file(path, f"Auto: add {f.name}", content)
                except Exception as e:
                    logger.warning(f"GH upload failed for {f.name}: {e}")
            logger.info(f"📤 GH sync: {len(files)} reports")

        for kb_file in ["knowledge_graph.json", "virtual_ledger.json"]:
            kb_path = kb_dir / kb_file
            if kb_path.exists():
                try:
                    content = kb_path.read_text(encoding="utf-8")
                    path = f"knowledge_base/{kb_file}"
                    try:
                        existing = repo.get_contents(path)
                        repo.update_file(path, f"Auto: update {kb_file}", content, existing.sha)
                    except Exception:
                        repo.create_file(path, f"Auto: add {kb_file}", content)
                except Exception as e:
                    logger.warning(f"GH upload failed for {kb_file}: {e}")
        queue_path = kb_dir / "developer_queue.md"
        if queue_path.exists():
            try:
                content = queue_path.read_text(encoding="utf-8")
                path = "knowledge_base/developer_queue.md"
                try:
                    existing = repo.get_contents(path)
                    repo.update_file(path, "Auto: update developer queue", content, existing.sha)
                except Exception:
                    repo.create_file(path, "Auto: add developer queue", content)
            except Exception as e:
                logger.warning(f"GH developer queue upload failed: {e}")
        return 0
    except Exception as e:
        logger.error("GH sync error; inspect token scope and repository permissions")
        return 1


def main() -> int:
    """Run optional HF sync and independent GitHub sync."""
    rc = 0
    rc |= sync_hf_dataset()
    rc |= sync_github()
    return rc


if __name__ == "__main__":
    sys.exit(main())
