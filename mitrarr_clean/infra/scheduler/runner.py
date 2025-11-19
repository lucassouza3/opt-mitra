"""Contém o agendador responsável por executar jobs definidos em configuração."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

from infra.auto_recovery import RetryRunner


@dataclass(frozen=True, slots=True)
class ScheduledJob:
    """Representa uma entrada do agendador."""

    name: str
    command: Sequence[str]
    max_attempts: int = 1
    delay: float = 0.0


@dataclass(frozen=True)
class SchedulerResult:
    """Resultado da execução do lote de jobs."""

    success: bool
    successes: List[str]
    failures: List[str]


class JobScheduler:
    """Responsável por executar jobs sequencialmente."""

    def __init__(self) -> None:
        self._successes: list[str] = []
        self._failures: list[str] = []

    def run(self, jobs: Sequence[ScheduledJob]) -> SchedulerResult:
        """Executa os jobs informados e registra sucessos/falhas."""
        for job in jobs:
            runner = RetryRunner(max_attempts=job.max_attempts, delay_seconds=job.delay)

            def task() -> None:
                result = subprocess.run(list(job.command), check=False)
                if result.returncode != 0:
                    raise RuntimeError(f"Comando retornou {result.returncode}")

            retry_result = runner.run(task, label=job.name)
            if retry_result.success:
                self._successes.append(job.name)
            else:
                self._failures.append(job.name)

        return SchedulerResult(success=not self._failures, successes=self._successes, failures=self._failures)


def load_schedule(path: Path) -> list[ScheduledJob]:
    """Carrega um arquivo JSON contendo a definição dos jobs."""
    data = json.loads(path.read_text(encoding="utf-8"))
    jobs = []
    for item in data.get("jobs", []):
        jobs.append(
            ScheduledJob(
                name=item["name"],
                command=item["command"],
                max_attempts=item.get("max_attempts", 1),
                delay=item.get("delay", 0.0),
            )
        )
    return jobs
