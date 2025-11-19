"""Validador para comparar volumes processados com histórico recente."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass(frozen=True)
class VolumeAlert:
    """Representa um alerta de volume abaixo do esperado."""

    label: str
    expected: int
    current: int


class VolumeValidator:
    """Compara o volume atual com a média histórica mínima."""

    def __init__(self, history_path: Path, min_ratio: float) -> None:
        if min_ratio <= 0 or min_ratio > 1:
            raise ValueError("min_ratio deve estar entre 0 e 1.")
        self.history_path = history_path
        self.min_ratio = min_ratio
        if not self.history_path.exists():
            self.history_path.write_text("{}", encoding="utf-8")

    def _load_history(self) -> dict[str, int]:
        try:
            return json.loads(self.history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def validate(self, current_count: int, label: str) -> List[VolumeAlert]:
        """Retorna alertas quando o volume atual ultrapassa o limite inferior."""
        history = self._load_history()
        if not history:
            return []
        *_, last_value = history.values()
        threshold = last_value * self.min_ratio
        if current_count < threshold:
            return [VolumeAlert(label=label, expected=int(last_value), current=current_count)]
        return []
