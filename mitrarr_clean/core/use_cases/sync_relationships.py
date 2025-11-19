"""Caso de uso responsável por sincronizar relacionamentos processados."""

from __future__ import annotations

from typing import Sequence

from core.entities import RelationshipRecord
from core.exceptions import UseCaseError
from core.interfaces import RelationshipRepository


class SyncRelationshipsUseCase:
    """Persiste uma coleção de relacionamentos normalizados."""

    def __init__(self, repository: RelationshipRepository) -> None:
        """Armazena o repositório que realizará a sincronização."""
        self._repository = repository

    def execute(self, records: Sequence[RelationshipRecord]) -> int:
        """
        Sincroniza os relacionamentos e retorna a quantidade persistida.

        :raises ValueError: quando a lista está vazia.
        """
        if not records:
            raise ValueError("Não há relacionamentos para sincronizar.")

        try:
            return self._repository.sync(records)
        except Exception as exc:  # pragma: no cover
            raise UseCaseError("Falha ao sincronizar relacionamentos.") from exc
