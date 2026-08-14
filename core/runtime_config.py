"""Secret-safe runtime configuration helpers.

Credentials are read only from the process environment. This module never
writes secrets to disk and never returns raw values in diagnostic payloads.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


_PLACEHOLDERS = {
    "",
    "placeholder",
    "changeme",
    "replace_me",
    "your_token_here",
    "your_api_key_here",
    "hf_...",
    "ghp_...",
}


@dataclass(frozen=True)
class SecretStatus:
    """Non-sensitive status for one environment-backed credential."""

    name: str
    configured: bool
    shape_valid: bool
    source: str = "environment"

    @property
    def usable(self) -> bool:
        return self.configured and self.shape_valid

    def public_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "configured": self.configured,
            "shape_valid": self.shape_valid,
            "usable": self.usable,
            "source": self.source,
        }


def read_secret(name: str, *, environ: Mapping[str, str] | None = None) -> str:
    """Read a secret from the environment without fallback or persistence."""
    values = os.environ if environ is None else environ
    return str(values.get(name, "")).strip()


def is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return normalized in _PLACEHOLDERS or normalized.endswith("_placeholder")


def validate_secret(name: str, *, prefix: str | None = None, environ: Mapping[str, str] | None = None) -> SecretStatus:
    value = read_secret(name, environ=environ)
    configured = bool(value) and not is_placeholder(value)
    shape_valid = configured and (prefix is None or value.startswith(prefix))
    return SecretStatus(name=name, configured=configured, shape_valid=shape_valid)


def mask_secret(value: str) -> str:
    """Return a stable non-reversible display form for diagnostics."""
    if not value:
        return "<unset>"
    if len(value) <= 8:
        return "<configured>"
    return f"{value[:3]}…{value[-2:]}"


def runtime_secret_status(*, environ: Mapping[str, str] | None = None) -> dict[str, dict[str, object]]:
    """Return connection readiness without exposing credential values."""
    return {
        "HF_TOKEN": validate_secret("HF_TOKEN", prefix="hf_", environ=environ).public_dict(),
        "GITHUB_TOKEN": validate_secret("GITHUB_TOKEN", environ=environ).public_dict(),
        "OPENAI_API_KEY": validate_secret("OPENAI_API_KEY", prefix="sk-", environ=environ).public_dict(),
        "GROQ_API_KEY": validate_secret("GROQ_API_KEY", prefix="gsk_", environ=environ).public_dict(),
        "DEEPSEEK_API_KEY": validate_secret("DEEPSEEK_API_KEY", environ=environ).public_dict(),
        "GEMINI_API_KEY": validate_secret("GEMINI_API_KEY", environ=environ).public_dict(),
        "TOGETHER_API_KEY": validate_secret("TOGETHER_API_KEY", environ=environ).public_dict(),
        "FIREWORKS_API_KEY": validate_secret("FIREWORKS_API_KEY", environ=environ).public_dict(),
        "AIMLAPI_KEY": validate_secret("AIMLAPI_KEY", environ=environ).public_dict(),
    }
