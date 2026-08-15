#!/usr/bin/env python3
"""Static security gate for Nuclear Intelligence releases.

The audit intentionally reports locations and rule names only; it never prints
credential values. It is safe to run locally and in CI.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "env", ".gradio"}
TEXT_SUFFIXES = {".py", ".yml", ".yaml", ".json", ".toml", ".ini", ".cfg", ".env", ".template", ".md", ".txt"}
SECRET_PATTERNS = (
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("github_classic_pat", re.compile(r"ghp_[A-Za-z0-9]{20,}")),
    ("huggingface_token", re.compile(r"hf_[A-Za-z0-9]{20,}")),
    ("openai_key", re.compile(r"sk-[A-Za-z0-9]{20,}")),
)


def iter_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def audit() -> list[str]:
    findings: list[str] = []
    for path in iter_files():
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        relative = path.relative_to(ROOT)
        for rule, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append(f"{rule}:{relative}")
        if path.name == ".env" or path.name.endswith(".env.local"):
            findings.append(f"tracked_environment_file:{relative}")
        if "allow_origins=[\"*\"]" in text and "CORS" in text:
            findings.append(f"wildcard_cors:{relative}")
    return sorted(set(findings))


def main() -> int:
    findings = audit()
    if findings:
        print("Security gate failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Security gate passed: no tracked credential patterns or forbidden runtime settings found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
