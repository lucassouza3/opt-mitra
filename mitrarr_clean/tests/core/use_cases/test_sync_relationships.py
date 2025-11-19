"""Testes para o caso de uso SyncRelationships."""

import pytest

from core.entities import RelationshipRecord
from core.use_cases import SyncRelationshipsUseCase
from core.exceptions import UseCaseError


class FakeRelationshipRepository:
    """Implementação em memória usada para verificar interações."""

    def __init__(self) -> None:
        self.saved: list[RelationshipRecord] = []

    def sync(self, items):
        self.saved.extend(items)
        return len(items)


class FailingRelationshipRepository(FakeRelationshipRepository):
    """Simula falhas ao escrever dados."""

    def sync(self, items):  # type: ignore[override]
        raise RuntimeError("db down")


def test_sync_relationships_persists_records() -> None:
    """Garante que os relacionamentos recebidos são repassados corretamente."""
    repo = FakeRelationshipRepository()
    use_case = SyncRelationshipsUseCase(repo)
    records = [
        RelationshipRecord(person_id="1", related_person_id="2", relation_type="FRIEND"),
        RelationshipRecord(person_id="2", related_person_id="3", relation_type="ALLY"),
    ]

    result = use_case.execute(records)

    assert result == 2
    assert repo.saved == records


def test_sync_relationships_requires_records() -> None:
    """Assegura que uma lista vazia gera erro."""
    repo = FakeRelationshipRepository()
    use_case = SyncRelationshipsUseCase(repo)

    with pytest.raises(ValueError):
        use_case.execute([])


def test_sync_relationships_wraps_failures() -> None:
    """Erro de repositório vira UseCaseError."""
    repo = FailingRelationshipRepository()
    use_case = SyncRelationshipsUseCase(repo)
    records = [RelationshipRecord(person_id="1", related_person_id="2", relation_type="ALLY")]

    with pytest.raises(UseCaseError):
        use_case.execute(records)
