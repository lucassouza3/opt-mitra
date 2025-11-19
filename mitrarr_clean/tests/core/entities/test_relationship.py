"""Testes para RelationshipRecord."""

import pytest

from core.entities import RelationshipRecord


def test_relationship_accepts_valid_data() -> None:
    """Instância válida precisa manter os valores informados."""
    record = RelationshipRecord(person_id="1", related_person_id="2", relation_type="ALLY")
    assert record.person_id == "1"
    assert record.related_person_id == "2"
    assert record.relation_type == "ALLY"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"person_id": "", "related_person_id": "2", "relation_type": "ALLY"},
        {"person_id": "1", "related_person_id": " ", "relation_type": "ALLY"},
        {"person_id": "1", "related_person_id": "2", "relation_type": " "},
    ],
)
def test_relationship_requires_all_fields(kwargs) -> None:
    """Campos vazios devem gerar ValueError."""
    with pytest.raises(ValueError):
        RelationshipRecord(**kwargs)
