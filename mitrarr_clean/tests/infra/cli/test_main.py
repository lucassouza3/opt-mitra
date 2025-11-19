"""Testes end-to-end da CLI."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Sequence

import pytest

from infra.cli.main import main
from infra.scheduler import SchedulerResult
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


def test_check_volume_command_flags_alert(tmp_path: Path) -> None:
    """Comando check-volume deve emitir alerta quando volume cai."""
    history = tmp_path / "history.json"
    history.write_text(json.dumps({"2025-01-01": 100}), encoding="utf-8")

    assert run_cli(
        [
            "check-volume",
            "--history",
            str(history),
            "--label",
            "detran",
            "--current",
            "40",
            "--ratio",
            "0.8",
        ]
    ) == 1


def test_check_volume_command_ok(tmp_path: Path) -> None:
    """Sem quedas relevantes, o comando retorna 0."""
    history = tmp_path / "history.json"
    history.write_text(json.dumps({"2025-01-01": 50}), encoding="utf-8")

    assert (
        run_cli(
            [
                "check-volume",
                "--history",
                str(history),
                "--label",
                "idnet",
                "--current",
                "45",
            ]
        )
        == 0
    )
def test_run_with_retry_executes_command(tmp_path: Path) -> None:
    """Comando run-with-retry executa scripts e retorna com sucesso."""
    script_path = tmp_path / "script.py"
    script_path.write_text("import sys\nsys.exit(0)\n", encoding="utf-8")
    args = [
        "run-with-retry",
        "--label",
        "dummy",
        "--max-attempts",
        "2",
        "--delay",
        "0",
        "--",
        sys.executable,
        str(script_path),
    ]
    assert run_cli(args) == 0
def test_run_with_retry_fails_when_command_fails(tmp_path: Path) -> None:
    """Quando o comando falha, o retorno deve ser 1."""
    script_path = tmp_path / "script.py"
    script_path.write_text("import sys\nsys.exit(1)\n", encoding="utf-8")
    args = [
        "run-with-retry",
        "--label",
        "dummy",
        "--max-attempts",
        "1",
        "--delay",
        "0",
        "--",
        sys.executable,
        str(script_path),
    ]
    assert run_cli(args) == 1


def test_run_with_retry_requires_command() -> None:
    """Sem comando informado, o CLI deve retornar erro."""
    args = [
        "run-with-retry",
        "--label",
        "dummy",
        "--max-attempts",
        "1",
        "--delay",
        "0",
    ]
    assert run_cli(args) == 1


def test_run_schedule_command(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """O comando run-schedule precisa carregar o arquivo e executar os jobs."""
    config = tmp_path / "schedule.json"
    config.write_text(
        json.dumps(
            {
                "jobs": [
                    {"name": "a", "command": ["echo", "a"]},
                ]
            }
        ),
        encoding="utf-8",
    )

    captured: dict[str, list[str]] = {}

    class DummyScheduler:
        def run(self, jobs):
            captured["jobs"] = [job.name for job in jobs]
            return SchedulerResult(success=True, successes=captured["jobs"], failures=[])

    monkeypatch.setattr("infra.cli.main.JobScheduler", lambda: DummyScheduler())

    result = run_cli(["run-schedule", "--config", str(config)])
    assert result == 0
    assert captured["jobs"] == ["a"]


def test_run_schedule_handles_empty_config(tmp_path: Path) -> None:
    """Quando a configuração está vazia, deve retornar 0 e aceitar ausência de jobs."""
    config = tmp_path / "schedule.json"
    config.write_text(json.dumps({"jobs": []}), encoding="utf-8")

    class DummyScheduler:
        def run(self, jobs):
            return SchedulerResult(success=True, successes=[], failures=[])

    result = run_cli(["run-schedule", "--config", str(config)])
    assert result == 0


def test_run_schedule_reports_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Falhas devem fazer o comando retornar 1."""
    config = tmp_path / "schedule.json"
    config.write_text(json.dumps({"jobs": [{"name": "fail", "command": ["x"]}]}), encoding="utf-8")

    class DummyScheduler:
        def run(self, jobs):
            return SchedulerResult(success=False, successes=[], failures=["fail"])

    monkeypatch.setattr("infra.cli.main.JobScheduler", lambda: DummyScheduler())

    assert run_cli(["run-schedule", "--config", str(config)]) == 1


def test_emit_alert_creates_entry(tmp_path: Path) -> None:
    """O comando emit-alert precisa registrar a mensagem no log."""
    args = [
        "emit-alert",
        "--type",
        "manual",
        "--job",
        "job_a",
        "--severity",
        "info",
        "--message",
        "Teste",
    ]
    result = run_cli(args)
    assert result == 0
    log_file = Path(get_data_dir()) / "logs" / "alerts.log"
    assert "manual" in log_file.read_text(encoding="utf-8")
