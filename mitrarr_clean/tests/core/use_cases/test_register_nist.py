"""Testes para o caso de uso RegisterNist."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from core.use_cases import RegisterNistInput, RegisterNistUseCase
from core.exceptions import UseCaseError
from core.entities import NistFile


class InMemoryNistRepository:
    """Implementação simples usada nos testes."""

    def __init__(self) -> None:
        self._items: dict[str, NistFile] = {}

    def exists(self, identifier: str) -> bool:
        return identifier in self._items

    def save(self, nist: NistFile) -> None:
        self._items[nist.identifier] = nist

    def get_pending(self, limit: int):
        return list(self._items.values())[:limit]

    def mark_as_sent(self, identifiers):
        for identifier in identifiers:
            self._items.pop(identifier, None)


class FailingNistRepository(InMemoryNistRepository):
    """Simula falhas durante a persistência."""

    def save(self, nist: NistFile) -> None:  # type: ignore[override]
        raise RuntimeError("db error")


def test_register_nist_persists_new_record(tmp_path: Path) -> None:
    """Confere se o repositório recebe o novo registro."""
    repository = InMemoryNistRepository()
    use_case = RegisterNistUseCase(repository)

    path = tmp_path / "novo.nst"
    path.write_text("conteudo")

    input_data = RegisterNistInput(
        identifier="ID1",
        source="DETRAN",
        path=path,
        created_at=datetime.now(UTC),
    )

    result = use_case.execute(input_data)

    assert repository.exists("ID1")
    assert result.identifier == "ID1"


def test_register_nist_blocks_duplicates(tmp_path: Path) -> None:
    """Garante que um identificador duplicado gera erro."""
    repository = InMemoryNistRepository()
    use_case = RegisterNistUseCase(repository)

    path = tmp_path / "duplicado.nst"
    path.write_text("conteudo")

    input_data = RegisterNistInput(
        identifier="ID1",
        source="DETRAN",
        path=path,
        created_at=datetime.now(UTC),
    )

    use_case.execute(input_data)

    with pytest.raises(ValueError):
        use_case.execute(input_data)


def test_register_nist_wraps_repository_errors(tmp_path: Path) -> None:
    """Um erro do repositório deve ser convertido em UseCaseError."""
    repository = FailingNistRepository()
    use_case = RegisterNistUseCase(repository)
    path = tmp_path / "erro.nst"
    path.write_text("conteudo")
    input_data = RegisterNistInput(
        identifier="ID1",
        source="SISMIGRA",
        path=path,
        created_at=datetime.now(UTC),
    )

    with pytest.raises(UseCaseError):
        use_case.execute(input_data)
