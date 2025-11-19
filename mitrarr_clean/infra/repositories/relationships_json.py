"""Repositório de relacionamentos baseado em arquivo JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

from core.entities import RelationshipRecord
from core.interfaces import RelationshipRepository


class JsonRelationshipRepository(RelationshipRepository):
    """Persiste relacionamentos em um arquivo simples para auditoria."""

    def __init__(self, base_dir: Path) -> None:
        """Cria o arquivo se ainda não existir."""
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = self._base_dir / "relationships.json"
        if not self._db_path.exists():
            self._db_path.write_text("[]", encoding="utf-8")

    def _load(self) -> list[dict]:
        return json.loads(self._db_path.read_text(encoding="utf-8"))

    def _dump(self, data: list[dict]) -> None:
        self._db_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def sync(self, items: Sequence[RelationshipRecord]) -> int:
        """Acrescenta os relacionamentos e retorna a quantidade inserida."""
        data = self._load()
        for record in items:
            data.append(
                {
                    "person_id": record.person_id,
                    "related_person_id": record.related_person_id,
                    "relation_type": record.relation_type,
                }
            )
        self._dump(data)
        return len(items)
