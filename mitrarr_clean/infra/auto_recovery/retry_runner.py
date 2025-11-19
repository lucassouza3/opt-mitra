"""Implementação simples de tentativas automáticas (auto-recovery)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class RetryResult:
    """Representa o resultado da tentativa de executar uma tarefa."""

    success: bool
    attempts: int
    label: str


class RetryRunner:
    """Executa uma função com um número limitado de tentativas."""

    def __init__(self, max_attempts: int, delay_seconds: float) -> None:
        if max_attempts <= 0:
            raise ValueError("max_attempts deve ser positivo.")
        if delay_seconds < 0:
            raise ValueError("delay_seconds não pode ser negativo.")
        self.max_attempts = max_attempts
        self.delay_seconds = delay_seconds

    def run(self, task: Callable[[], None], label: str) -> RetryResult:
        """Executa a tarefa até que tenha sucesso ou atinja o número máximo de tentativas."""
        attempts = 0
        while attempts < self.max_attempts:
            attempts += 1
            try:
                task()
                return RetryResult(success=True, attempts=attempts, label=label)
            except Exception:
                if attempts >= self.max_attempts:
                    break
                time.sleep(self.delay_seconds)
        return RetryResult(success=False, attempts=attempts, label=label)
