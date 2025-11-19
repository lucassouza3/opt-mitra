"""Representa relacionamentos entre registros internos e externos."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RelationshipRecord:
    """Modelo para transportar relacionamentos normalizados entre pessoas."""

    person_id: str
    related_person_id: str
    relation_type: str

    def __post_init__(self) -> None:
        """Garante que todos os campos foram preenchidos corretamente."""
        if not self.person_id.strip():
            raise ValueError("person_id não pode ser vazio.")
        if not self.related_person_id.strip():
            raise ValueError("related_person_id não pode ser vazio.")
        if not self.relation_type.strip():
            raise ValueError("relation_type não pode ser vazio.")
