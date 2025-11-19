"""Caso de uso responsável por registrar novos arquivos NIST no sistema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.entities import NistFile
from core.interfaces import NistRepository
from core.exceptions import UseCaseError


@dataclass(slots=True)
class RegisterNistInput:
    """Estrutura de dados para entrada do caso de uso RegisterNist."""

    identifier: str
    source: str
    path: Path
    created_at: datetime


class RegisterNistUseCase:
    """Registra um novo NIST garantindo unicidade e validações de domínio."""

    def __init__(self, repository: NistRepository) -> None:
        """Recebe a dependência necessária para persistir o registro."""
        self._repository = repository

    def execute(self, data: RegisterNistInput) -> NistFile:
        """
        Processa a entrada e persiste o registro.

        :raises ValueError: quando o identificador já existe.
        """
        nist = NistFile(
            identifier=data.identifier,
            source=data.source,
            path=data.path,
            created_at=data.created_at,
        )

        if self._repository.exists(nist.identifier):
            raise ValueError(f"O NIST {nist.identifier} já foi registrado.")

        try:
            self._repository.save(nist)
        except Exception as exc:  # pragma: no cover - guard to wrap repository issues
            raise UseCaseError("Falha ao salvar o NIST no repositório.") from exc
        return nist
