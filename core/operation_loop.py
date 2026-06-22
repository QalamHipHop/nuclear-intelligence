"""
Nuclear Intelligence v5.0 - Operation Loop
Re-exports the v4 operation loop for backward compatibility.
"""

from core.operation_loop_v4 import (
    OperationLoop,
    OperationLoopConfig,
    OperationCycleResult,
)

__all__ = ["OperationLoop", "OperationLoopConfig", "OperationCycleResult"]
