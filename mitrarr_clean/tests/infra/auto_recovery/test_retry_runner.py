"""Testes para o mecanismo simples de auto-recovery."""

from __future__ import annotations

from pathlib import Path

import pytest

from infra.auto_recovery.retry_runner import RetryRunner, RetryResult


class DummyTask:
    """Simula uma tarefa que falha N vezes antes de ter sucesso."""

    def __init__(self, failures_before_success: int) -> None:
        self.failures_remaining = failures_before_success
        self.invocations = 0

    def __call__(self) -> None:
        self.invocations += 1
        if self.failures_remaining > 0:
            self.failures_remaining -= 1
            raise RuntimeError("temporary failure")


def test_retry_runner_succeeds_after_retries(tmp_path: Path) -> None:
    """Uma falha temporária deve ser recuperada automaticamente."""
    task = DummyTask(failures_before_success=2)
    runner = RetryRunner(max_attempts=5, delay_seconds=0)

    result = runner.run(task, label="job_a")

    assert result == RetryResult(success=True, attempts=3, label="job_a")
    assert task.invocations == 3


def test_retry_runner_reports_failure(tmp_path: Path) -> None:
    """Quando todas as tentativas falham, deve retornar erro."""
    task = DummyTask(failures_before_success=5)
    runner = RetryRunner(max_attempts=3, delay_seconds=0)

    result = runner.run(task, label="job_b")

    assert result.success is False
    assert result.attempts == 3


def test_retry_runner_invalid_attempts() -> None:
    """max_attempts precisa ser positivo."""
    with pytest.raises(ValueError):
        RetryRunner(max_attempts=0, delay_seconds=0)


def test_retry_runner_invalid_delay() -> None:
    """delay_seconds não pode ser negativo."""
    with pytest.raises(ValueError):
        RetryRunner(max_attempts=1, delay_seconds=-1)
