"""Gateway que simula o envio ao FindFace gravando logs locais."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from core.entities import NistFile
from core.interfaces import FindFaceGateway


class LogFileFindFaceGateway(FindFaceGateway):
    """Registra cada envio em um arquivo para fins de auditoria."""

    def __init__(self, base_dir: Path) -> None:
        """Garante que o diretório de logs exista."""
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._log_path = self._base_dir / "findface.log"

    def send_nists(self, nists: Sequence[NistFile]) -> None:
        """Escreve cada ID enviado em formato legível."""
        with self._log_path.open("a", encoding="utf-8") as log_file:
            for item in nists:
                log_file.write(
                    f"{datetime.now(UTC).isoformat()} SENT {item.identifier} SOURCE={item.source}\n"
                )
