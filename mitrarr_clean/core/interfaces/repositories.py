"""Interfaces de repositórios utilizados pelos casos de uso."""

from __future__ import annotations

from typing import Iterable, Protocol, Sequence

from core.entities import NistFile, RelationshipRecord


class NistRepository(Protocol):
    """Define operações de acesso aos registros NIST."""

    def exists(self, identifier: str) -> bool:
        """Retorna True se o identificador informado já estiver persistido."""

    def save(self, nist: NistFile) -> None:
        """Persiste um novo registro NIST."""

    def get_pending(self, limit: int) -> Sequence[NistFile]:
        """Obtém registros ainda não enviados ao FindFace."""

    def mark_as_sent(self, identifiers: Iterable[str]) -> None:
        """Atualiza o status dos registros enviados com sucesso."""


class RelationshipRepository(Protocol):
    """Define o contrato para sincronização de relacionamentos."""

    def sync(self, items: Sequence[RelationshipRecord]) -> int:
        """
        Persiste ou atualiza os relacionamentos informados.

        :return: quantidade de registros sincronizados.
        """
