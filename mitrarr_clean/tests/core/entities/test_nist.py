"""Testes do modelo NistFile."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from core.entities import NistFile


def test_nistfile_accepts_valid_data(tmp_path: Path) -> None:
    """Garante que valores válidos geram uma instância estável."""
    sample_file = tmp_path / "teste.nst"
    sample_file.write_text("conteudo")

    nist = NistFile(
        identifier="ABC123",
        source="DETRAN",
        path=sample_file,
        created_at=datetime.now(UTC),
    )

    assert nist.identifier == "ABC123"
    assert nist.path == sample_file


@pytest.mark.parametrize(
    ("identifier", "source", "extension"),
    [
        ("", "SRC", ".nst"),
        ("ID", "", ".nst"),
        ("ID", "SRC", ".txt"),
    ],
)
def test_nistfile_invalid_values_raise(identifier: str, source: str, extension: str, tmp_path: Path) -> None:
    """Verifica se erros são lançados quando há dados inválidos."""
    sample_file = tmp_path / f"arquivo{extension}"
    sample_file.write_text("conteudo")

    with pytest.raises(ValueError):
        NistFile(
            identifier=identifier,
            source=source,
            path=sample_file,
            created_at=datetime.now(UTC),
        )


def test_nistfile_created_at_cannot_be_future(tmp_path: Path) -> None:
    """Valida a proteção contra datas futuras."""
    sample_file = tmp_path / "future.nst"
    sample_file.write_text("conteudo")

    with pytest.raises(ValueError):
        NistFile(
            identifier="ID",
            source="SRC",
            path=sample_file,
            created_at=datetime.now(UTC) + timedelta(days=1),
        )
