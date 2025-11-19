"""Gerador simples de alertas para monitoramento."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True)
class Alert:
    """Representa um alerta gerado por qualquer rotina."""

    alert_type: str
    job: str
    severity: str
    message: str


class AlertDispatcher:
    """Responsável por registrar alertas em um arquivo."""

    def __init__(self, log_path: Path) -> None:
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, alert: Alert) -> None:
        """Escreve o alerta como JSON com timestamp UTC."""
        payload = {
            "type": alert.alert_type,
            "job": alert.job,
            "severity": alert.severity,
            "message": alert.message,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False))
            log_file.write("\n")
