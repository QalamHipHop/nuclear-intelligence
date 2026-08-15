"""Build and validate the curated Hugging Face Space bundle.

The Space is generated from the canonical repository runtime. This prevents the
public UI from carrying a second research engine or a stale safety/evaluation
implementation.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parent.parent
BUNDLE_ITEMS = (
    "core",
    "blockchain",
    "scripts",
    "knowledge_base",
    "core_hf.py",
    "requirements.txt",
)


def _copy_item(source: Path, destination: Path) -> None:
    target = destination / source.name
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env"))
    else:
        shutil.copy2(source, target)


def _write_dockerfile(destination: Path) -> None:
    dockerfile = destination / "Dockerfile"
    dockerfile.write_text(
        """FROM python:3.11-slim\n\nWORKDIR /app\nCOPY requirements.txt .\nRUN pip install --no-cache-dir -r requirements.txt\nCOPY . .\nENV GRADIO_PORT=7860\nENV HF_SPACE=true\nENV AUTO_START_LOOP=false\nEXPOSE 7860\nCMD [\"python\", \"app.py\"]\n""",
        encoding="utf-8",
    )


def _validate_bundle(destination: Path) -> None:
    required = ("app.py", "core_hf.py", "core/runtime.py", "core/operation_loop_v4.py", "core/research_controller.py", "blockchain/virtual_ledger.py", "requirements.txt", "Dockerfile")
    missing = [item for item in required if not (destination / item).exists()]
    if missing:
        raise RuntimeError(f"Space bundle is missing required files: {', '.join(missing)}")

    entrypoint = (destination / "app.py").read_text(encoding="utf-8")
    forbidden = ("class NuclearIntelligenceCore", "class LLMEngine", "def _autonomous_loop")
    leaked = [marker for marker in forbidden if marker in entrypoint]
    if leaked:
        raise RuntimeError(f"Space entrypoint contains duplicate runtime implementation: {', '.join(leaked)}")
    if "from core_hf import get_adapter" not in entrypoint:
        raise RuntimeError("Space entrypoint must import the canonical core_hf adapter")


def build_bundle(destination: Path) -> Path:
    destination = destination.resolve()
    if destination == ROOT:
        raise ValueError("Refusing to write the generated Space bundle into the project root")
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)

    for item in BUNDLE_ITEMS:
        source = ROOT / item
        if not source.exists():
            raise RuntimeError(f"Cannot build Space bundle; required source is missing: {item}")
        _copy_item(source, destination)

    shutil.copy2(ROOT / "hf_deploy" / "space_app.py", destination / "app.py")
    shutil.copy2(ROOT / "hf_deploy" / "README.md", destination / "README.md")
    _write_dockerfile(destination)
    _validate_bundle(destination)
    return destination


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the canonical Hugging Face Space bundle")
    parser.add_argument("--output", default=str(ROOT / ".space_build"), help="Destination directory for the generated bundle")
    args = parser.parse_args(list(argv) if argv is not None else None)
    bundle = build_bundle(Path(args.output))
    print(f"Space bundle ready: {bundle}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
