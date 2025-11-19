"""Testes end-to-end da CLI."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Sequence

import pytest

from infra.cli.main import main
from infra.container import get_data_dir


@pytest.fixture(autouse=True)
def ensure_tmp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Direciona o CLI para um diretório temporário em cada teste."""
    monkeypatch.setenv("MITRARR_DATA_DIR", str(tmp_path))
    yield
    monkeypatch.delenv("MITRARR_DATA_DIR", raising=False)


def run_cli(args: Sequence[str]) -> int:
    """Facilita a execução do CLI nos testes."""
    return main(list(args))


def test_register_and_send_flow(tmp_path: Path) -> None:
    """Registra um arquivo e envia para o FindFace, validando logs e persistência."""
    file_path = tmp_path / "sample.nst"
    file_path.write_text("conteudo")

    result = run_cli(
        [
            "register-nist",
            "--id",
            "NIST-1",
            "--source",
            "SISMIGRA",
            "--file",
            str(file_path),
        ]
    )
    assert result == 0

    result = run_cli(["send-to-findface", "--batch-size", "10"])
    assert result == 0

    data_dir = Path(get_data_dir())
    log_file = data_dir / "logs" / "findface.log"
    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    assert "NIST-1" in log_content


def test_register_duplicate_returns_error(tmp_path: Path) -> None:
    """Um mesmo ID não pode ser registrado duas vezes."""
    file_path = tmp_path / "dup.nst"
    file_path.write_text("conteudo")
    args = [
        "register-nist",
        "--id",
        "DUP",
        "--source",
        "DETRAN",
        "--file",
        str(file_path),
    ]
    assert run_cli(args) == 0
    assert run_cli(args) == 1


def test_sync_relationships_with_file(tmp_path: Path) -> None:
    """Sincroniza um lote de relacionamentos via JSON."""
    payload = [{"person_id": "1", "related_person_id": "2", "relation_type": "ALLY"}]
    rel_file = tmp_path / "rels.json"
    rel_file.write_text(json.dumps(payload), encoding="utf-8")

    result = run_cli(["sync-relationships", "--input", str(rel_file)])
    assert result == 0

    data_dir = Path(get_data_dir())
    rel_db = data_dir / "relationships" / "relationships.json"
    assert rel_db.exists()
    stored = json.loads(rel_db.read_text(encoding="utf-8"))
    assert stored == payload


def test_sync_relationships_invalid_payload_returns_error(tmp_path: Path) -> None:
    """Arquivos inválidos precisam retornar erro apropriado."""
    rel_file = tmp_path / "invalid.json"
    rel_file.write_text("{}", encoding="utf-8")
    assert run_cli(["sync-relationships", "--input", str(rel_file)]) == 1
