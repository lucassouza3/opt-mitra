"""API REST simples para acompanhar os jobs do scheduler."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, List

from fastapi import FastAPI, HTTPException

from infra.scheduler import ScheduledJob


@dataclass
class JobState:
    """Representa um job e seu estado de pausa."""

    job: ScheduledJob
    paused: bool = False


@dataclass
class JobStateStore:
    """Armazena os jobs e permite pausar/resumir."""

    jobs: Iterable[ScheduledJob]
    _states: List[JobState] = field(init=False)

    def __post_init__(self) -> None:
        self._states = [JobState(job=job) for job in self.jobs]

    def to_dict(self) -> List[dict]:
        """Converte para formato serializável."""
        return [
            {
                "name": state.job.name,
                "command": list(state.job.command),
                "paused": state.paused,
            }
            for state in self._states
        ]

    def _get_state(self, name: str) -> JobState:
        for state in self._states:
            if state.job.name == name:
                return state
        raise KeyError(name)

    def pause(self, name: str) -> bool:
        state = self._get_state(name)
        state.paused = True
        return state.paused

    def resume(self, name: str) -> bool:
        state = self._get_state(name)
        state.paused = False
        return state.paused


def create_app(store: JobStateStore) -> FastAPI:
    """Cria a aplicação FastAPI a partir de um store."""
    app = FastAPI(title="MITRARR Scheduler API")

    @app.get("/jobs")
    def list_jobs() -> dict:
        return {"jobs": store.to_dict()}

    @app.post("/jobs/{name}/pause")
    def pause_job(name: str) -> dict:
        try:
            paused = store.pause(name)
        except KeyError:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        return {"name": name, "paused": paused}

    @app.post("/jobs/{name}/resume")
    def resume_job(name: str) -> dict:
        try:
            paused = store.resume(name)
        except KeyError:
            raise HTTPException(status_code=404, detail="Job não encontrado")
        return {"name": name, "paused": paused}

    return app
