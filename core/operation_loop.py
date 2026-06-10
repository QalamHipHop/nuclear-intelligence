"""Nuclear Intelligence - Operation Loop v2.0
Autonomous research-to-tokenization with developer mode"""
import time, os, json, threading, hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from loguru import logger
from dataclasses import dataclass

from core.nuclear_intelligence import NuclearIntelligenceCore, ResearchQuestion, ResearchAnswer, EvaluationScore
from blockchain.virtual_ledger import VirtualLedger

@dataclass
class OperationLoopConfig:
    interval_minutes: int = 30; min_accuracy: float = 93.0; min_novelty: float = 70.0
    min_usefulness: float = 75.0; min_overall: float = 82.0; auto_start: bool = True
    questions_per_cycle: int = 1; developer_mode: bool = False; web_search_enabled: bool = True; save_reports: bool = True

@dataclass
class OperationCycleResult:
    cycle_id: str; timestamp: str; question: Dict; answer: Dict; evaluation: Dict
    minted: bool; tx_hash: Optional[str] = None; developer_analysis: Optional[Dict] = None
    execution_time_seconds: float = 0.0
    def to_dict(self): return {"cycle_id": self.cycle_id, "timestamp": self.timestamp, "question": self.question, "answer": self.answer, "evaluation": self.evaluation, "minted": self.minted, "tx_hash": self.tx_hash, "developer_analysis": self.developer_analysis, "execution_time_seconds": self.execution_time_seconds}

class OperationLoop:
    def __init__(self, core: NuclearIntelligenceCore, ledger: VirtualLedger, config: Optional[OperationLoopConfig] = None):
        self.core = core; self.ledger = ledger
        self.config = config or OperationLoopConfig()
        self.history: List[OperationCycleResult] = []; self.is_running = False; self._thread: Optional[threading.Thread] = None
        self._load_history()

    def _load_history(self):
        reports_dir = "reports"
        if os.path.exists(reports_dir):
            try:
                for filename in sorted([f for f in os.listdir(reports_dir) if f.startswith("cycle_") and f.endswith(".json")], reverse=True)[:100]:
                    try:
                        with open(os.path.join(reports_dir, filename)) as f:
                            d = json.load(f)
                            self.history.append(OperationCycleResult(d.get("cycle_id",filename), d.get("timestamp",""), d.get("question",{}), d.get("answer",{}), d.get("evaluation",{}), d.get("minted",False), d.get("tx_hash"), d.get("developer_analysis"), d.get("execution_time_seconds",0)))
                    except: pass
                logger.info(f"Loaded {len(self.history)} history records")
            except: pass

    def _should_mint(self, evaluation: EvaluationScore) -> bool:
        overall = evaluation.overall_score()
        checks = {"accuracy": evaluation.scientific_accuracy >= self.config.min_accuracy, "novelty": evaluation.novelty_score >= self.config.min_novelty, "usefulness": evaluation.usefulness_score >= self.config.min_usefulness, "overall": overall >= self.config.min_overall, "consistency": evaluation.self_consistency_check}
        passed = sum(checks.values())
        logger.info(f"Minting: {passed}/{len(checks)} | Acc={evaluation.scientific_accuracy:.1f} Novel={evaluation.novelty_score:.1f} Use={evaluation.usefulness_score:.1f} Overall={overall:.1f}")
        return all([checks["overall"], checks["consistency"]])

    def run_cycle(self, developer_mode: bool = False) -> OperationCycleResult:
        cycle_id = hashlib.sha256(datetime.now().isoformat().encode()).hexdigest()[:12]
        start = time.time()
        logger.info(f"=== Cycle {cycle_id} ===")
        try:
            q = self.core.generate_question()
            if not q: raise RuntimeError("Question generation failed")
            answer = self.core.conduct_research(q, use_web_search=self.config.web_search_enabled)
            if not answer: raise RuntimeError("Research generation failed")
            evaluation = self.core.evaluate_answer(q, answer)
            dev_analysis = None
            if developer_mode or self.config.developer_mode:
                logger.info("Developer mode analysis...")
                dev_analysis = self.core.developer_mode_analysis(q, answer)
            minted = False; tx_hash = None
            if self._should_mint(evaluation):
                logger.info("Minting NES token...")
                self.core.integrate_knowledge(q, answer, evaluation)
                tx_hash = self.ledger.mint_nes_token({"cycle_id": cycle_id, "question": q.to_dict(), "evaluation": evaluation.to_dict(), "summary": answer.answer[:500]})
                minted = True
            else:
                self.core.reject_answer(evaluation)
            elapsed = round(time.time() - start, 2)
            result = OperationCycleResult(cycle_id, datetime.now().isoformat(), q.to_dict(), answer.to_dict(), evaluation.to_dict(), minted, tx_hash, dev_analysis, elapsed)
            self.history.append(result)
            if self.config.save_reports: self._save_report(result)
            logger.info(f"=== Cycle {cycle_id} | {'✅ Minted' if minted else '❌ Rejected'} | {elapsed}s ===")
            return result
        except Exception as e:
            logger.error(f"Cycle {cycle_id} failed: {e}")
            if self.config.save_reports: self._save_report(OperationCycleResult(cycle_id, datetime.now().isoformat(), {"error": str(e)}, {}, {}, False, None, None, round(time.time()-start,2)), is_error=True)
            raise

    def _save_report(self, result: OperationCycleResult, is_error: bool = False):
        try:
            os.makedirs("reports", exist_ok=True)
            prefix = "cycle_error" if is_error else "cycle"
            with open(f"reports/{prefix}_{result.cycle_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f: json.dump(result.to_dict(), f, indent=4, ensure_ascii=False)
        except: pass

    def start(self):
        if self.is_running: return
        self.is_running = True
        logger.info(f"Loop started. Interval: {self.config.interval_minutes} min, Threshold: {self.config.min_accuracy}%")
        def loop():
            while self.is_running:
                try: self.run_cycle(developer_mode=self.config.developer_mode)
                except: pass
                if self.is_running: time.sleep(self.config.interval_minutes * 60)
        self._thread = threading.Thread(target=loop, daemon=True); self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread: self._thread.join(timeout=5)
        logger.info("Loop stopped")

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.history); minted = sum(1 for r in self.history if r.minted)
        total_time = sum(r.execution_time_seconds for r in self.history)
        return {"total_cycles": total, "tokens_minted": minted, "tokens_rejected": total - minted, "approval_rate": f"{(minted/max(total,1)*100):.1f}%", "average_cycle_time": f"{(total_time/max(total,1)):.1f}s", "is_running": self.is_running, "config": {"interval_minutes": self.config.interval_minutes, "min_accuracy": self.config.min_accuracy, "developer_mode": self.config.developer_mode}}

    def get_recent_cycles(self, limit: int = 10) -> List[Dict]:
        return [r.to_dict() for r in self.history[-limit:]]
