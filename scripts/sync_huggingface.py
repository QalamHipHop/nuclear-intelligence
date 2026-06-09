#!/usr/bin/env python3
"""
Sync project with Hugging Face Space and datasets.
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

try:
    from huggingface_hub import HfApi
except ImportError:
    logger.warning("huggingface_hub not installed, skipping HF sync")
    sys.exit(0)


def main():
    """Sync with Hugging Face."""
    logger.info("Starting Hugging Face synchronization...")
    
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_KEY")
    if not hf_token:
        logger.warning("HF_TOKEN or HUGGINGFACE_API_KEY not set, skipping sync")
        return 0
    
    try:
        api = HfApi(token=hf_token)
        
        # Get user info
        user_info = api.whoami()
        logger.info(f"Authenticated as: {user_info['name']}")
        
        # Sync reports and exports
        logger.info("Syncing reports and exports...")
        
        reports_dir = Path(__file__).parent.parent / "reports"
        exports_dir = Path(__file__).parent.parent / "exports"
        
        # Create dataset repo if needed
        dataset_repo_id = "Qalam/nuclear-intelligence-dataset"
        
        try:
            logger.info(f"Syncing to dataset: {dataset_repo_id}")
            
            # Upload reports
            if reports_dir.exists():
                for report_file in reports_dir.glob("*.json"):
                    logger.info(f"Uploading report: {report_file.name}")
                    api.upload_file(
                        path_or_fileobj=str(report_file),
                        path_in_repo=f"reports/{report_file.name}",
                        repo_id=dataset_repo_id,
                        repo_type="dataset"
                    )
            
            # Upload exports
            if exports_dir.exists():
                for export_file in exports_dir.glob("*.json"):
                    logger.info(f"Uploading export: {export_file.name}")
                    api.upload_file(
                        path_or_fileobj=str(export_file),
                        path_in_repo=f"exports/{export_file.name}",
                        repo_id=dataset_repo_id,
                        repo_type="dataset"
                    )
            
            logger.info("Hugging Face sync completed successfully!")
            
        except Exception as e:
            logger.warning(f"Could not sync to dataset: {e}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Hugging Face sync error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
