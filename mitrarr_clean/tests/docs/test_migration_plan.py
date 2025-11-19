"""Garante que o migration plan contém as seções esperadas."""

from pathlib import Path


def test_migration_plan_mentions_cron_and_rollback() -> None:
    """Documento precisa citar cron, alerta e rollback."""
    path = Path(__file__).resolve().parents[2] / "docs" / "migration_plan.md"
    content = path.read_text(encoding="utf-8")
    assert "crontab" in content.lower()
    assert "rollback" in content.lower()
    assert "emit-alert" in content
