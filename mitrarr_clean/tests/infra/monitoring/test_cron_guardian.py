"""Testes para o utilitário cron_guardian."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from infra.monitoring.heartbeats import HeartbeatMonitor
from infra.monitoring.cron_guardian import main


def test_cron_guardian_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Nenhum job atrasado deve resultar em retorno 0."""
    monkeypatch.setenv("MITRARR_DATA_DIR", str(tmp_path))
    monitor = HeartbeatMonitor(tmp_path / "monitoring" / "heartbeats.json")
    monitor.record("job_a")

    assert main([]) == 0


def test_cron_guardian_flags_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Jobs sem heartbeat há mais tempo que o threshold resultam em erro."""
    monkeypatch.setenv("MITRARR_DATA_DIR", str(tmp_path))
    monitor = HeartbeatMonitor(tmp_path / "monitoring" / "heartbeats.json")
    monitor._dump({"job_a": (datetime.now(UTC) - timedelta(days=10)).isoformat()})

    assert main(["--threshold-days", "7"]) == 1
