"""Registro de heartbeats para jobs agendados."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable


def default_clock() -> datetime:
    """Retorna o horário atual em UTC."""
    return datetime.now(UTC)


@dataclass
class HeartbeatMonitor:
    """Gerencia o armazenamento do último horário de execução de cada job."""

    storage_path: Path
    clock: Callable[[], datetime] = default_clock

    def __post_init__(self) -> None:
        """Garante que o arquivo exista e contenha uma estrutura válida."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, str]:
        """Lê o conteúdo do arquivo JSON."""
        data = json.loads(self.storage_path.read_text(encoding="utf-8"))
        return {str(key): str(value) for key, value in data.items()}

    def _dump(self, data: dict[str, str]) -> None:
        """Salva os dados atualizados."""
        self.storage_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def record(self, job_name: str) -> None:
        """Atualiza o horário de execução do job informado."""
        normalized = job_name.strip()
        if not normalized:
            raise ValueError("job_name não pode ser vazio.")
        data = self._load()
        data[normalized] = self.clock().isoformat()
        self._dump(data)

    def get_last_run(self, job_name: str) -> datetime | None:
        """Retorna o horário registrado para o job ou None."""
        data = self._load()
        raw = data.get(job_name)
        if not raw:
            return None
        return datetime.fromisoformat(raw)

    def get_stale_jobs(self, threshold: timedelta) -> list[str]:
        """Lista os jobs cujo último heartbeat é mais antigo que o threshold."""
        limit = self.clock() - threshold
        stale = []
        for job, iso_ts in self._load().items():
            try:
                ts = datetime.fromisoformat(iso_ts)
            except ValueError:
                stale.append(job)
                continue
            if ts < limit:
                stale.append(job)
        return stale
