"""Testes para a API de controle do scheduler."""

from __future__ import annotations

from fastapi.testclient import TestClient

from infra.api.server import JobStateStore, create_app
from infra.scheduler import ScheduledJob


def build_client() -> tuple[TestClient, JobStateStore]:
    jobs = [
        ScheduledJob(name="job_a", command=["echo", "a"]),
        ScheduledJob(name="job_b", command=["echo", "b"]),
    ]
    store = JobStateStore(jobs=jobs)
    app = create_app(store)
    return TestClient(app), store


def test_list_jobs_returns_structure() -> None:
    """A listagem precisa trazer nome/comando/estado pausado."""
    client, _ = build_client()
    response = client.get("/jobs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["jobs"][0]["name"] == "job_a"
    assert payload["jobs"][0]["paused"] is False


def test_pause_and_resume_job() -> None:
    """Pausar e retomar um job deve atualizar o estado."""
    client, _ = build_client()

    pause = client.post("/jobs/job_a/pause")
    assert pause.status_code == 200
    assert pause.json()["paused"] is True

    resume = client.post("/jobs/job_a/resume")
    assert resume.status_code == 200
    assert resume.json()["paused"] is False


def test_pause_unknown_job_returns_404() -> None:
    """Jobs inexistentes precisam retornar 404."""
    client, _ = build_client()
    response = client.post("/jobs/unknown/pause")
    assert response.status_code == 404


def test_resume_unknown_job_returns_404() -> None:
    """Resumir job inexistente também gera 404."""
    client, _ = build_client()
    response = client.post("/jobs/unknown/resume")
    assert response.status_code == 404
