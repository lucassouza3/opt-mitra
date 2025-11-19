"""Testes para o monitor de heartbeats (última execução de cada job)."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Iterator

import pytest

from infra.monitoring.heartbeats import HeartbeatMonitor


class FrozenClock:
    """Permite controlar o tempo retornado nas chamadas."""

    def __init__(self, start: datetime) -> None:
        self._current = start

    def tick(self, delta: timedelta) -> None:
        self._current += delta

    def __call__(self) -> datetime:
        return self._current


@pytest.fixture()
def clock() -> Iterator[FrozenClock]:
    frozen = FrozenClock(datetime(2025, 1, 1, 0, 0, 0))
    yield frozen


def test_record_and_retrieve_last_run(tmp_path: Path, clock: FrozenClock) -> None:
    """Garante que o monitor grava e recupera os horários corretamente."""
    monitor = HeartbeatMonitor(tmp_path / "heartbeats.json", clock=clock)
    monitor.record("job_a")

    assert monitor.get_last_run("job_a") == datetime(2025, 1, 1, 0, 0, 0)
    assert monitor.get_last_run("job_b") is None


def test_stale_jobs_detect_values_above_threshold(tmp_path: Path, clock: FrozenClock) -> None:
    """Verifica se jobs atrasados são marcados corretamente."""
    monitor = HeartbeatMonitor(tmp_path / "heartbeats.json", clock=clock)
    monitor.record("job_a")
    clock.tick(timedelta(days=8))
    monitor.record("job_b")

    stale = monitor.get_stale_jobs(threshold=timedelta(days=7))
    assert stale == ["job_a"]


def test_monitor_handles_empty_storage(tmp_path: Path, clock: FrozenClock) -> None:
    """Leitura inicial deve retornar estrutura vazia."""
    monitor = HeartbeatMonitor(tmp_path / "hb.json", clock=clock)
    assert monitor.get_stale_jobs(timedelta(days=7)) == []


def test_record_rejects_empty_name(tmp_path: Path, clock: FrozenClock) -> None:
    """job_name vazio não deve ser aceito."""
    monitor = HeartbeatMonitor(tmp_path / "hb.json", clock=clock)
    with pytest.raises(ValueError):
        monitor.record(" ")


def test_stale_jobs_marks_invalid_entries(tmp_path: Path, clock: FrozenClock) -> None:
    """Entradas inválidas no arquivo precisam ser consideradas atrasadas."""
    monitor = HeartbeatMonitor(tmp_path / "hb.json", clock=clock)
    monitor._dump({"job_a": "invalid-date"})
    assert monitor.get_stale_jobs(timedelta(days=7)) == ["job_a"]
