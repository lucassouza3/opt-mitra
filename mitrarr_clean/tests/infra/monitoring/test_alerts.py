"""Testes para o gerenciador de alertas."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from types import SimpleNamespace
from pathlib import Path

from infra.monitoring.alerts import Alert, AlertDispatcher


def test_dispatcher_writes_json_line(tmp_path: Path, monkeypatch) -> None:
    """Envio de alertas deve registrar entradas JSON."""
    log_file = tmp_path / "alerts.log"
    dispatcher = AlertDispatcher(log_file)

    fixed_now = datetime(2025, 1, 1, tzinfo=UTC)
    monkeypatch.setattr("infra.monitoring.alerts.datetime", SimpleNamespace(now=lambda tz=None: fixed_now))

    alert = Alert(
        alert_type="volume_drop",
        job="adiciona_nists",
        severity="high",
        message="Volume atual 20% do esperado",
    )

    dispatcher.send(alert)

    content = log_file.read_text(encoding="utf-8").strip()
    payload = json.loads(content)
    assert payload["type"] == "volume_drop"
    assert payload["job"] == "adiciona_nists"
    assert payload["severity"] == "high"
    assert payload["message"] == "Volume atual 20% do esperado"
    assert payload["timestamp"] == fixed_now.isoformat()


def test_dispatcher_append_multiple(tmp_path: Path) -> None:
    """Enviar múltiplos alertas deve gerar múltiplas linhas."""
    log_file = tmp_path / "alerts.log"
    dispatcher = AlertDispatcher(log_file)

    dispatcher.send(Alert(alert_type="cron", job="job1", severity="info", message="Ok"))
    dispatcher.send(Alert(alert_type="cron", job="job2", severity="warning", message="Delay"))

    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
