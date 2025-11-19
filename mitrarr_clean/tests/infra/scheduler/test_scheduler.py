"""Testes para o scheduler responsável por substituir os antigos check_and_run."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from infra.scheduler import (
    JobScheduler,
    SchedulerResult,
    ScheduledJob,
    load_schedule,
)


def test_scheduler_runs_all_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Todas as tarefas devem ser executadas em ordem quando não há falhas."""
    executed: list[list[str]] = []

    def fake_run(cmd, check: bool = False):  # type: ignore[override]
        executed.append(cmd)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("infra.scheduler.runner.subprocess.run", fake_run)

    scheduler = JobScheduler()
    jobs = [
        ScheduledJob(name="job1", command=["echo", "1"]),
        ScheduledJob(name="job2", command=["echo", "2"]),
    ]

    result = scheduler.run(jobs)

    assert result == SchedulerResult(success=True, successes=["job1", "job2"], failures=[])
    assert executed == [["echo", "1"], ["echo", "2"]]


def test_scheduler_collects_failed_jobs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Falhas após as tentativas devem ser reportadas."""
    executed: list[str] = []

    def fake_run(cmd, check: bool = False):  # type: ignore[override]
        executed.append(cmd[1])
        return SimpleNamespace(returncode=1 if "fail" in cmd else 0)

    monkeypatch.setattr("infra.scheduler.runner.subprocess.run", fake_run)

    scheduler = JobScheduler()
    jobs = [
        ScheduledJob(name="job_ok", command=["echo", "ok"]),
        ScheduledJob(name="job_fail", command=["echo", "fail"], max_attempts=2),
    ]

    result = scheduler.run(jobs)

    assert result.success is False
    assert result.failures == ["job_fail"]
    assert result.successes == ["job_ok"]


def test_load_schedule_from_json(tmp_path: Path) -> None:
    """Carregar JSON deve gerar a lista de ScheduledJob equivalente."""
    config = {
        "jobs": [
            {"name": "a", "command": ["echo", "1"]},
            {"name": "b", "command": ["python", "script.py"], "max_attempts": 3, "delay": 1.5},
        ]
    }
    config_path = tmp_path / "schedule.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    jobs = load_schedule(config_path)

    assert jobs[0] == ScheduledJob(name="a", command=["echo", "1"])
    assert jobs[1] == ScheduledJob(name="b", command=["python", "script.py"], max_attempts=3, delay=1.5)
