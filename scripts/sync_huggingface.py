#!/usr/bin/env python3
"""Nuclear Intelligence - HuggingFace & GitHub Sync"""
import os, sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from loguru import logger

try:
    from huggingface_hub import HfApi, create_repo
except ImportError:
    logger.warning("huggingface_hub not installed")
    sys.exit(0)


def sync_huggingface():
    logger.info("Starting HF sync...")
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
    if not hf_token or hf_token in ("", "hf_placeholder"):
        logger.warning("HF_TOKEN not set, skipping")
        return 0

    try:
        api = HfApi(token=hf_token)
        user = api.whoami()
        logger.info(f"Authenticated as: {user['name']}")

        dataset_repo = "Qalam/nuclear-intelligence-dataset"
        try:
            create_repo(repo_id=dataset_repo, repo_type="dataset", token=hf_token, exist_ok=True)
        except Exception as e:
            logger.warning(f"Repo creation: {e}")

        reports_dir = Path(__file__).parent.parent / "reports"
        kb_dir = Path(__file__).parent.parent / "knowledge_base"

        for report_file in sorted(reports_dir.glob("cycle_*.json"))[-10:]:
            try:
                api.upload_file(path_or_fileobj=str(report_file), path_in_repo=f"reports/{report_file.name}",
                               repo_id=dataset_repo, repo_type="dataset")
                logger.info(f"Uploaded: {report_file.name}")
            except Exception as e:
                logger.warning(f"Failed: {report_file.name}: {e}")

        kg_file = kb_dir / "knowledge_graph.json"
        if kg_file.exists():
            try:
                api.upload_file(path_or_fileobj=str(kg_file), path_in_repo="knowledge_graph.json",
                               repo_id=dataset_repo, repo_type="dataset")
                logger.info("KG uploaded")
            except: pass

        logger.info("HF sync completed!")
        return 0
    except Exception as e:
        logger.error(f"HF sync error: {e}")
        return 1


def sync_github():
    logger.info("Starting GitHub sync...")
    token = os.getenv("GITHUB_TOKEN")
    if not token or token == "ghp_placeholder":
        logger.warning("GITHUB_TOKEN not set, skipping")
        return 0

    try:
        from github import Github
        g = Github(token)
        repo = g.get_repo(os.getenv("GITHUB_REPO", "QalamHipHop/nuclear-intelligence"))
        reports_dir = Path(__file__).parent.parent / "reports"
        for report_file in sorted(reports_dir.glob("cycle_*.json"))[-5:]:
            try:
                content = report_file.read_text()
                path = f"reports/{report_file.name}"
                try:
                    existing = repo.get_contents(path)
                    repo.update_file(path, f"Update {report_file.name}", content, existing.sha)
                except:
                    repo.create_file(path, f"Add {report_file.name}", content)
                logger.info(f"Synced: {path}")
            except Exception as e:
                logger.warning(f"Failed: {report_file.name}: {e}")
        logger.info("GitHub sync completed!")
        return 0
    except ImportError:
        logger.warning("PyGithub not installed")
        return 0
    except Exception as e:
        logger.error(f"GitHub sync error: {e}")
        return 1


if __name__ == "__main__":
    result = 0
    result |= sync_huggingface()
    result |= sync_github()
    sys.exit(result)
