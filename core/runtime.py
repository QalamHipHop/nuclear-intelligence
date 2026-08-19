"""Canonical runtime composition for every Nuclear Intelligence entrypoint.

All execution surfaces (CLI, API, scheduled jobs and Space adapters) should
obtain configuration from this module instead of rebuilding it independently.
Secrets remain environment-backed through runtime_config.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from blockchain.virtual_ledger import VirtualLedger
from core.nuclear_intelligence import NuclearIntelligenceCore
from core.operation_loop import OperationLoop, OperationLoopConfig


DEFAULT_PROVIDER_CHAIN = (
    "huggingface",
    "deepseek",
    "groq",
    "gemini",
    "together",
    "fireworks",
    "aimlapi",
)


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class RuntimeSettings:
    """Validated, non-secret application settings shared by all entrypoints."""

    root: Path
    reports_dir: Path
    knowledge_base_dir: Path
    ledger_path: Path
    knowledge_graph_path: Path
    vector_db_path: Path
    hf_dataset_repo: str
    provider_chain: tuple[str, ...]
    developer_mode: bool
    web_search_enabled: bool
    min_accuracy: float
    min_novelty: float
    min_usefulness: float
    min_overall: float
    min_completeness: float
    max_retries: int
    retry_delay: int
    pow_difficulty: int
    sync_to_hf: bool
    sync_to_github: bool
    evaluation_samples: int
    evaluation_agreement_threshold: float
    public_max_query_chars: int
    public_rate_limit_per_minute: int
    public_cycle_enabled: bool

    @classmethod
    def from_environment(cls, root: str | Path | None = None) -> "RuntimeSettings":
        project_root = Path(root or os.getenv("NI_PROJECT_ROOT", Path.cwd())).resolve()
        kb = project_root / "knowledge_base"
        configured = tuple(
            p.strip() for p in os.getenv("LLM_PROVIDER_CHAIN", "").split(",") if p.strip()
        )
        return cls(
            root=project_root,
            reports_dir=project_root / "reports",
            knowledge_base_dir=kb,
            ledger_path=kb / "virtual_ledger.json",
            knowledge_graph_path=kb / "knowledge_graph.json",
            vector_db_path=kb / "faiss_index",
            hf_dataset_repo=os.getenv("HF_DATASET_REPO", "Qalam/nuclear-intelligence-dataset"),
            provider_chain=configured or DEFAULT_PROVIDER_CHAIN,
            developer_mode=_env_bool("DEVELOPER_MODE", True),
            web_search_enabled=_env_bool("WEB_SEARCH_ENABLED", True),
            min_accuracy=_env_float("MIN_ACCURACY", 70.0),
            min_novelty=_env_float("MIN_NOVELTY", 60.0),
            min_usefulness=_env_float("MIN_USEFULNESS", 60.0),
            min_overall=_env_float("MIN_OVERALL", 65.0),
            min_completeness=_env_float("MIN_COMPLETENESS", 40.0),
            max_retries=_env_int("MAX_RETRIES", 3),
            retry_delay=_env_int("RETRY_DELAY_SECONDS", 5),
            pow_difficulty=_env_int("POW_DIFFICULTY", 3),
            # GitHub is the default durable source of truth; HF is opt-in.
            # GitHub is the durable source of truth; HF sync is opt-in.
            sync_to_hf=_env_bool("SYNC_TO_HF", False),
            sync_to_github=_env_bool("SYNC_TO_GITHUB", True),
            evaluation_samples=max(1, _env_int("EVALUATION_SAMPLES", 2)),
            evaluation_agreement_threshold=min(1.0, max(0.0, _env_float("EVALUATION_AGREEMENT_THRESHOLD", 0.80))),
            public_max_query_chars=min(4000, max(100, _env_int("PUBLIC_MAX_QUERY_CHARS", 2000))),
            public_rate_limit_per_minute=min(120, max(1, _env_int("PUBLIC_RATE_LIMIT_PER_MINUTE", 20))),
            # Public visitors may read/search/ask safely, but cannot trigger durable
            # autonomous cycles unless an operator explicitly enables this setting.
            public_cycle_enabled=_env_bool("PUBLIC_CYCLE_ENABLED", False),
        )

    def ensure_directories(self) -> None:
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_dir.mkdir(parents=True, exist_ok=True)

    def loop_config(self) -> OperationLoopConfig:
        return OperationLoopConfig(
            interval_minutes=_env_int("OPERATION_LOOP_INTERVAL_MINUTES", 30),
            min_accuracy=self.min_accuracy,
            min_novelty=self.min_novelty,
            min_usefulness=self.min_usefulness,
            min_overall=self.min_overall,
            min_completeness=self.min_completeness,
            questions_per_cycle=1,
            developer_mode=self.developer_mode,
            web_search_enabled=self.web_search_enabled,
            save_reports=True,
            max_retries=self.max_retries,
            retry_delay=self.retry_delay,
            sync_to_hf=self.sync_to_hf,
            sync_to_gh=self.sync_to_github,
            evaluation_samples=self.evaluation_samples,
            evaluation_agreement_threshold=self.evaluation_agreement_threshold,
        )


def build_runtime(settings: RuntimeSettings | None = None) -> tuple[NuclearIntelligenceCore, OperationLoop, VirtualLedger, RuntimeSettings]:
    """Construct the canonical core, loop and ledger with shared paths/config."""
    cfg = settings or RuntimeSettings.from_environment()
    cfg.ensure_directories()
    core = NuclearIntelligenceCore(
        vector_db_path=str(cfg.vector_db_path),
        kg_path=str(cfg.knowledge_graph_path),
        provider_chain=list(cfg.provider_chain),
    )
    ledger = VirtualLedger(
        ledger_file=str(cfg.ledger_path),
        difficulty=cfg.pow_difficulty,
    )
    loop = OperationLoop(core=core, ledger=ledger, config=cfg.loop_config())
    return core, loop, ledger, cfg


def runtime_public_status(settings: RuntimeSettings | None = None) -> dict[str, Any]:
    """Return non-secret operational status for health endpoints and diagnostics."""
    cfg = settings or RuntimeSettings.from_environment()
    return {
        "runtime": "canonical",
        # Deliberately omit absolute filesystem paths and secret diagnostics from
        # public responses. The service exposes capability/status metadata only.
        "provider_chain": list(cfg.provider_chain),
        "sync": {"huggingface": cfg.sync_to_hf, "github": cfg.sync_to_github},
        "thresholds": {
            "accuracy": cfg.min_accuracy,
            "novelty": cfg.min_novelty,
            "usefulness": cfg.min_usefulness,
            "overall": cfg.min_overall,
            "completeness": cfg.min_completeness,
            "evaluation_samples": cfg.evaluation_samples,
            "evaluation_agreement_threshold": cfg.evaluation_agreement_threshold,
            "public_max_query_chars": cfg.public_max_query_chars,
            "public_rate_limit_per_minute": cfg.public_rate_limit_per_minute,
            "public_cycle_enabled": cfg.public_cycle_enabled,
        },
    }
