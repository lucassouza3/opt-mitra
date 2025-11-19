"""Testes para o caso de uso SendToFindFace."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Sequence

import pytest

from core.entities import NistFile
from core.use_cases import SendToFindFaceUseCase
from core.exceptions import UseCaseError


class DummyNistRepository:
    """Repositório simplificado utilizado nos testes."""

    def __init__(self, pending: Sequence[NistFile]) -> None:
        self._pending = list(pending)
        self.sent: list[str] = []

    def exists(self, identifier: str) -> bool:
        return any(item.identifier == identifier for item in self._pending)

    def save(self, nist: NistFile) -> None:
        self._pending.append(nist)

    def get_pending(self, limit: int):
        return self._pending[:limit]

    def mark_as_sent(self, identifiers: Iterable[str]) -> None:
        self.sent.extend(identifiers)
        self._pending = [item for item in self._pending if item.identifier not in identifiers]


class DummyFindFaceGateway:
    """Gateway que apenas grava quais registros foram enviados."""

    def __init__(self) -> None:
        self.last_payload: Sequence[NistFile] = []

    def send_nists(self, nists: Sequence[NistFile]) -> None:
        self.last_payload = list(nists)


class FailingGateway(DummyFindFaceGateway):
    """Simula indisponibilidade do FindFace."""

    def send_nists(self, nists: Sequence[NistFile]) -> None:  # type: ignore[override]
        raise RuntimeError("gateway down")


class FailingMarkRepository(DummyNistRepository):
    """Repositório que falha ao marcar registros enviados."""

    def mark_as_sent(self, identifiers: Iterable[str]) -> None:  # type: ignore[override]
        raise RuntimeError("update failed")


def build_nist(identifier: str, tmp_path: Path) -> NistFile:
    """Cria um NistFile válido para os testes."""
    file_path = tmp_path / f"{identifier}.nst"
    file_path.write_text("conteudo")
    return NistFile(
        identifier=identifier,
        source="SISMIGRA",
        path=file_path,
        created_at=datetime.now(UTC),
    )


def test_send_to_findface_sends_and_marks(tmp_path: Path) -> None:
    """Garante que itens enviados são marcados como concluídos."""
    nists = [build_nist("ID1", tmp_path), build_nist("ID2", tmp_path)]
    repository = DummyNistRepository(nists)
    gateway = DummyFindFaceGateway()
    use_case = SendToFindFaceUseCase(repository, gateway)

    sent_count = use_case.execute(batch_size=10)

    assert sent_count == 2
    assert repository.sent == ["ID1", "ID2"]
    assert len(repository.get_pending(10)) == 0
    assert [item.identifier for item in gateway.last_payload] == ["ID1", "ID2"]


def test_send_to_findface_handles_empty(tmp_path: Path) -> None:
    """Retorna zero quando não existem pendências."""
    repository = DummyNistRepository([])
    gateway = DummyFindFaceGateway()
    use_case = SendToFindFaceUseCase(repository, gateway)

    assert use_case.execute(batch_size=5) == 0


def test_send_to_findface_validates_batch_size(tmp_path: Path) -> None:
    """Impede valores inválidos de batch_size."""
    repository = DummyNistRepository([])
    gateway = DummyFindFaceGateway()
    use_case = SendToFindFaceUseCase(repository, gateway)

    with pytest.raises(ValueError):
        use_case.execute(batch_size=0)


def test_send_to_findface_raises_when_gateway_fails(tmp_path: Path) -> None:
    """Erros do gateway devem ser reportados como UseCaseError."""
    nists = [build_nist("ID1", tmp_path)]
    repository = DummyNistRepository(nists)
    gateway = FailingGateway()
    use_case = SendToFindFaceUseCase(repository, gateway)

    with pytest.raises(UseCaseError):
        use_case.execute(batch_size=1)


def test_send_to_findface_raises_when_mark_fails(tmp_path: Path) -> None:
    """Falhas ao marcar envios devem gerar UseCaseError."""
    nists = [build_nist("ID1", tmp_path)]
    repository = FailingMarkRepository(nists)
    gateway = DummyFindFaceGateway()
    use_case = SendToFindFaceUseCase(repository, gateway)

    with pytest.raises(UseCaseError):
        use_case.execute(batch_size=1)
