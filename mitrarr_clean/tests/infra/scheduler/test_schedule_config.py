"""Garante que o template de schedule pode ser carregado."""

from pathlib import Path

from infra.scheduler import load_schedule


def test_schedule_template_is_valid() -> None:
    """O arquivo JSON de template precisa gerar uma lista de jobs."""
    config_path = Path(__file__).resolve().parents[3] / "configs" / "schedule_template.json"
    jobs = load_schedule(config_path)
    names = [job.name for job in jobs]
    assert "adiciona-nists" in names
    assert "envia-findface" in names
    assert len(jobs) >= 3
