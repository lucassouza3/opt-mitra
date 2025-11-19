"""Define a entidade que representa um arquivo NIST processado pelo MITRARR."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class NistFile:
    """Modelo imutável responsável por guardar metadados essenciais de um arquivo NIST."""

    identifier: str
    source: str
    path: Path
    created_at: datetime

    def __post_init__(self) -> None:
        """Executa validações básicas em cada atributo instanciado."""
        if not self.identifier or not self.identifier.strip():
            raise ValueError("Identificador do NIST não pode ser vazio.")
        if not self.source or not self.source.strip():
            raise ValueError("Fonte do NIST não pode ser vazia.")
        if self.path.suffix.lower() != ".nst":
            raise ValueError("Somente arquivos com extensão .nst são aceitos.")
        if self.created_at > datetime.now(UTC):
            raise ValueError("O campo created_at não pode estar no futuro.")
