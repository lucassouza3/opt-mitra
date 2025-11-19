"""Testes para o validador de volume processado."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from infra.monitoring.volume_guard import VolumeValidator, VolumeAlert


def write_history(path: Path, data: dict[str, int]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def test_volume_validator_detects_drop(tmp_path: Path) -> None:
    """Quando o volume atual fica abaixo do limite, deve retornar alerta."""
    history_path = tmp_path / "history.json"
    write_history(history_path, {"2025-01-01": 100, "2025-01-02": 80})

    validator = VolumeValidator(history_path, min_ratio=0.5)
    alerts = validator.validate(current_count=30, label="detran")

    assert alerts == [VolumeAlert(label="detran", expected=80, current=30)]


def test_volume_validator_handles_empty_history(tmp_path: Path) -> None:
    """Sem histórico, nenhum alerta deve ser gerado."""
    history_path = tmp_path / "history.json"
    validator = VolumeValidator(history_path, min_ratio=0.5)
    assert validator.validate(10, "idnet") == []


def test_volume_validator_respects_ratio(tmp_path: Path) -> None:
    """Se o volume estiver dentro do limite, não deve haver alerta."""
    history_path = tmp_path / "history.json"
    write_history(history_path, {"2025-01-01": 100})
    validator = VolumeValidator(history_path, min_ratio=0.5)
    assert validator.validate(60, "idnet") == []


def test_volume_validator_handles_invalid_ratio(tmp_path: Path) -> None:
    """Valores inválidos de min_ratio devem gerar erro."""
    history_path = tmp_path / "history.json"
    with pytest.raises(ValueError):
        VolumeValidator(history_path, min_ratio=2)


def test_volume_validator_handles_corrupted_history(tmp_path: Path) -> None:
    """Histórico inválido não deve quebrar a execução."""
    history_path = tmp_path / "history.json"
    history_path.write_text("invalid", encoding="utf-8")
    validator = VolumeValidator(history_path, min_ratio=0.5)
    assert validator.validate(10, "idnet") == []
