"""Repositório de NISTs baseado em arquivos JSON locais."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence

from core.entities import NistFile
from core.interfaces import NistRepository


class JsonNistRepository(NistRepository):
    """Persiste metadados de NISTs em um arquivo JSON simples."""

    def __init__(self, base_dir: Path) -> None:
        """Inicializa o repositório garantindo a existência do diretório/base."""
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._base_dir / "nists.json"
        if not self._db_path.exists():
            self._db_path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        """Carrega o conteúdo atual do armazenamento."""
        return json.loads(self._db_path.read_text(encoding="utf-8"))

    def _dump(self, data: list[dict]) -> None:
        """Salva o conteúdo atualizado."""
        self._db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def exists(self, identifier: str) -> bool:
        """Retorna True se o identificador informado já estiver persistido."""
        normalized = identifier.strip()
        return any(item["identifier"] == normalized for item in self._load())

    def save(self, nist: NistFile) -> None:
        """Persiste um novo registro NIST."""
        data = self._load()
        data.append(
            {
                "identifier": nist.identifier,
                "source": nist.source,
                "path": str(nist.path),
                "created_at": nist.created_at.isoformat(),
                "sent": False,
            }
        )
        self._dump(data)

    def get_pending(self, limit: int) -> Sequence[NistFile]:
        """Obtém registros ainda não enviados ao FindFace."""
        pending = [
            item for item in self._load() if not item.get("sent")  # type: ignore[arg-type]
        ]
        slice_items = pending[:limit]
        return [
            NistFile(
                identifier=item["identifier"],
                source=item["source"],
                path=Path(item["path"]),
                created_at=datetime.fromisoformat(item["created_at"]),
            )
            for item in slice_items
        ]

    def mark_as_sent(self, identifiers: Iterable[str]) -> None:
        """Atualiza o status dos registros enviados com sucesso."""
        ids = {identifier.strip() for identifier in identifiers}
        data = self._load()
        for item in data:
            if item["identifier"] in ids:
                item["sent"] = True
        self._dump(data)
