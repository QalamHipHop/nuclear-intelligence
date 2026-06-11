"""
Nuclear Intelligence v1.0.0 - Advanced Operation Loop
═══════════════════════════════════════════════════════════════════
Autonomous research-to-tokenization with:
- Multi-stage pipeline
- Intelligent retry logic
- Error recovery
- Comprehensive reporting
- Developer mode with deep analysis
═══════════════════════════════════════════════════════════════════
"""

import time
import os
import json
import threading
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
from dataclasses import dataclass, field

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from blockchain.virtual_ledger import VirtualLedger


@dataclass
class OperationLoopConfig:
    """Configuration for the operation loop"""
    interval_minutes: int = 30
    min_accuracy: float = 93.0
    min_novelty: float = 70.0
    min_usefulness: float = 75.0
    min_overall: float = 82.0
    min_completeness: float = 50.0
    auto_start: bool = True
    questions_per_cycle: int = 1
    developer_mode: bool = True
    web_search_enabled: bool = True
    save_reports: bool = True
    max_retries: int = 3
    retry_delay: int = 10


@dataclass
class OperationCycleResult:
    """Result of a single operation cycle"""
    cycle_id: str
    timestamp: str
    question: Dict
    answer: Dict
    evaluation: Dict
    minted: bool
    tx_hash: Optional[str] = None
    developer_analysis: Optional[Dict] = None
    execution_time_seconds: float = 0.0
    retry_count: int = 0
    error: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp,
            "question": self.question,
            "answer": self.answer,
            "evaluation": self.evaluation,
            "minted": self.minted,
            "tx_hash": self.tx_hash,
            "developer_analysis": self.developer_analysis,
            "execution_time_seconds": self.execution_time_seconds,
            "retry_count": self.retry_count,
            "error": self.error,
        }


class OperationLoop:
    """Advanced autonomous research loop"""

    def __init__(
        self,
        core: NuclearIntelligenceCore,
        ledger: VirtualLedger,
        config: Optional[OperationLoopConfig] = None,
    ):
        self.core = core
        self.ledger = ledger
        self.config = config or OperationLoopConfig()
        self.history: List[OperationCycleResult] = []
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._total_cycles = 0
        self._successful_cycles = 0

        self._load_history()
        logger.info(f"⚙️ Operation Loop initialized: interval={self.config.interval_minutes}min, threshold={self.config.min_accuracy}%")

    def _load_history(self):
        """Load cycle history from reports directory"""
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            try:
                files = sorted(
                    [f for f in os.listdir(reports_dir) if f.startswith("cycle_") and f.endswith(".json")],
                    reverse=True
                )[:200]  # Load last 200

                for filename in files:
                    try:
                        with open(os.path.join(reports_dir, filename), 'r', encoding='utf-8') as f:
                            d = json.load(f)
                            self.history.append(OperationCycleResult(
                                cycle_id=d.get("cycle_id", filename),
                                timestamp=d.get("timestamp", ""),
                                question=d.get("question", {}),
                                answer=d.get("answer", {}),
                                evaluation=d.get("evaluation", {}),
                                minted=d.get("minted", False),
                                tx_hash=d.get("tx_hash"),
                                developer_analysis=d.get("developer_analysis"),
                                execution_time_seconds=d.get("execution_time_seconds", 0),
                                retry_count=d.get("retry_count", 0),
                                error=d.get("error"),
                            ))
                    except Exception as e:
                        logger.warning(f"Failed to load {filename}: {e}")

                logger.info(f"📜 Loaded {len(self.history)} history records")
            except Exception as e:
                logger.warning(f"History loading failed: {e}")

    def _should_mint(self, evaluation: EvaluationScore) -> Dict[str, Any]:
        """Determine if answer should be minted"""
        overall = evaluation.overall_score()

        checks = {
            "accuracy": evaluation.scientific_accuracy >= self.config.min_accuracy,
            "novelty": evaluation.novelty_score >= self.config.min_novelty,
            "usefulness": evaluation.usefulness_score >= self.config.min_usefulness,
            "completeness": evaluation.completeness >= self.config.min_completeness,
            "overall": overall >= self.config.min_overall,
            "consistency": evaluation.self_consistency_check,
        }

        passed = sum(checks.values())
        total = len(checks)
        threshold_pct = (passed / total) * 100

        should_mint = checks["overall"] and checks["consistency"]

        logger.info(
            f"📊 Minting Check: {passed}/{total} ({threshold_pct:.0f}%) | "
            f"Acc={evaluation.scientific_accuracy:.1f}% Novel={evaluation.novelty_score:.1f}% "
            f"Use={evaluation.usefulness_score:.1f}% Overall={overall:.1f}% → "
            f"{'✅ MINT' if should_mint else '❌ REJECT'}"
        )

        return {"should_mint": should_mint, "checks": checks, "passed": passed, "total": total, "overall": overall}

    def run_cycle(self, developer_mode: bool = False, force_category: str = "") -> OperationCycleResult:
        """Execute a single research cycle with retry logic"""
        cycle_id = hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:16]
        start_time = time.time()

        logger.info(f"══════════════════════════════════════")
        logger.info(f"🔄 CYCLE {cycle_id} STARTING")
        logger.info(f"══════════════════════════════════════")

        retry_count = 0
        last_error = None

        while retry_count <= self.config.max_retries:
            try:
                # Step 1: Generate Question
                logger.info(f"📝 Step 1: Generating question...")
                question = self.core.generate_question(category_hint=force_category)
                if not question:
                    raise RuntimeError("Question generation failed")

                # Step 2: Conduct Research
                logger.info(f"🔬 Step 2: Conducting research...")
                answer = self.core.conduct_research(
                    question,
                    use_web_search=self.config.web_search_enabled
                )
                if not answer:
                    raise RuntimeError("Research generation failed")

                # Step 3: Evaluate Answer
                logger.info(f"📊 Step 3: Evaluating answer...")
                evaluation = self.core.evaluate_answer(question, answer)

                # Step 4: Developer Mode Analysis
                dev_analysis = None
                if developer_mode or self.config.developer_mode:
                    logger.info(f"🔬 Step 4: Developer mode analysis...")
                    dev_analysis = self.core.developer_mode_analysis(question, answer)

                # Step 5: Mint or Reject
                logger.info(f"💰 Step 5: Minting decision...")
                mint_check = self._should_mint(evaluation)
                minted = False
                tx_hash = None

                if mint_check["should_mint"]:
                    logger.info(f"🎉 Minting NES token...")
                    self.core.integrate_knowledge(question, answer, evaluation)
                    tx_hash = self.ledger.mint_nes_token({
                        "cycle_id": cycle_id,
                        "question": question.to_dict(),
                        "answer": answer.to_dict(),
                        "evaluation": evaluation.to_dict(),
                        "overall_score": mint_check["overall"],
                        "checks_passed": mint_check["passed"],
                        "provider": answer.provider,
                    })
                    minted = True
                else:
                    self.core.reject_answer(evaluation)

                # Calculate execution time
                elapsed = round(time.time() - start_time, 2)

                # Create result
                result = OperationCycleResult(
                    cycle_id=cycle_id,
                    timestamp=datetime.now().isoformat(),
                    question=question.to_dict(),
                    answer=answer.to_dict(),
                    evaluation=evaluation.to_dict(),
                    minted=minted,
                    tx_hash=tx_hash,
                    developer_analysis=dev_analysis,
                    execution_time_seconds=elapsed,
                    retry_count=retry_count,
                    error=None,
                )

                self.history.append(result)
                self._total_cycles += 1
                if minted:
                    self._successful_cycles += 1

                if self.config.save_reports:
                    self._save_report(result)

                logger.info(f"══════════════════════════════════════")
                logger.info(f"✅ CYCLE {cycle_id} COMPLETE | {'MINTED' if minted else 'REJECTED'} | {elapsed}s")
                logger.info(f"══════════════════════════════════════")

                return result

            except Exception as e:
                retry_count += 1
                last_error = str(e)
                logger.error(f"⚠️ Cycle {cycle_id} failed (attempt {retry_count}): {e}")

                if retry_count <= self.config.max_retries:
                    logger.info(f"🔄 Retrying in {self.config.retry_delay}s...")
                    time.sleep(self.config.retry_delay)
                else:
                    logger.error(f"❌ Cycle {cycle_id} failed after {retry_count} attempts")

        # All retries failed
        elapsed = round(time.time() - start_time, 2)
        result = OperationCycleResult(
            cycle_id=cycle_id,
            timestamp=datetime.now().isoformat(),
            question={"error": last_error},
            answer={},
            evaluation={},
            minted=False,
            tx_hash=None,
            developer_analysis=None,
            execution_time_seconds=elapsed,
            retry_count=retry_count,
            error=last_error,
        )

        self.history.append(result)
        self._total_cycles += 1

        if self.config.save_reports:
            self._save_report(result, is_error=True)

        return result

    def _save_report(self, result: OperationCycleResult, is_error: bool = False):
        """Save cycle report to disk"""
        try:
            os.makedirs("reports", exist_ok=True)
            prefix = "cycle_error" if is_error else "cycle_minted" if result.minted else "cycle_rejected"
            filename = f"reports/{prefix}_{result.cycle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result.to_dict(), f, indent=4, ensure_ascii=False)
            logger.debug(f"💾 Report saved: {filename}")
        except Exception as e:
            logger.error(f"Failed to save report: {e}")

    def start(self):
        """Start the autonomous loop"""
        if self.is_running:
            logger.warning("Loop already running")
            return

        self.is_running = True
        logger.info(f"▶️ Loop started: interval={self.config.interval_minutes}min, threshold={self.config.min_accuracy}%")

        def loop():
            while self.is_running:
                try:
                    self.run_cycle(developer_mode=self.config.developer_mode)
                except Exception as e:
                    logger.error(f"Cycle error: {e}")

                if self.is_running:
                    sleep_time = self.config.interval_minutes * 60
                    logger.info(f"😴 Sleeping for {sleep_time}s until next cycle...")
                    time.sleep(sleep_time)

        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the autonomous loop"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=10)
        logger.info("⏹️ Loop stopped")

    def pause(self):
        """Pause the loop (alias for stop)"""
        self.stop()

    def resume(self):
        """Resume the loop"""
        if not self.is_running:
            self.start()

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive loop statistics"""
        total = len(self.history)
        minted = sum(1 for r in self.history if r.minted)
        rejected = total - minted

        total_time = sum(r.execution_time_seconds for r in self.history)
        avg_time = total_time / max(total, 1)

        # Calculate success rate
        recent_cycles = self.history[-10:] if len(self.history) > 10 else self.history
        recent_minted = sum(1 for r in recent_cycles if r.minted)
        recent_rate = (recent_minted / max(len(recent_cycles), 1)) * 100

        return {
            "total_cycles": total,
            "tokens_minted": minted,
            "tokens_rejected": rejected,
            "approval_rate": f"{(minted / max(total, 1) * 100):.1f}%",
            "recent_approval_rate": f"{recent_rate:.1f}%",
            "average_cycle_time": f"{avg_time:.1f}s",
            "is_running": self.is_running,
            "config": {
                "interval_minutes": self.config.interval_minutes,
                "min_accuracy": self.config.min_accuracy,
                "min_novelty": self.config.min_novelty,
                "min_usefulness": self.config.min_usefulness,
                "min_overall": self.config.min_overall,
                "developer_mode": self.config.developer_mode,
                "web_search_enabled": self.config.web_search_enabled,
                "max_retries": self.config.max_retries,
            },
            "last_cycle": self.history[-1].to_dict() if self.history else None,
        }

    def get_recent_cycles(self, limit: int = 20) -> List[Dict]:
        """Get recent cycle results"""
        return [r.to_dict() for r in self.history[-limit:]]

    def get_cycle_by_id(self, cycle_id: str) -> Optional[OperationCycleResult]:
        """Get a specific cycle by ID"""
        for r in self.history:
            if r.cycle_id == cycle_id:
                return r
        return None

    def get_best_cycles(self, limit: int = 10) -> List[Dict]:
        """Get best performing cycles by overall score"""
        cycles_with_scores = []
        for r in self.history:
            eval_data = r.evaluation
            if eval_data:
                score = (
                    eval_data.get('scientific_accuracy', 0) * 0.45 +
                    eval_data.get('novelty_score', 0) * 0.25 +
                    eval_data.get('usefulness_score', 0) * 0.20
                )
                cycles_with_scores.append((score, r.to_dict()))

        cycles_with_scores.sort(key=lambda x: x[0], reverse=True)
        return [c[1] for _, c in cycles_with_scores[:limit]]


__all__ = ['OperationLoop', 'OperationLoopConfig', 'OperationCycleResult']