"""Configurações e contêiner simples para montar as dependências do MITRARR."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from core.use_cases import (
    RegisterNistInput,
    RegisterNistUseCase,
    SendToFindFaceUseCase,
    SyncRelationshipsUseCase,
)
from infra.gateways import LogFileFindFaceGateway
from infra.monitoring import HeartbeatMonitor
from infra.repositories import JsonNistRepository, JsonRelationshipRepository


@dataclass
class AppContainer:
    """Expõe os casos de uso prontos para serem utilizados pela CLI."""

    register_nist: RegisterNistUseCase
    send_to_findface: SendToFindFaceUseCase
    sync_relationships: SyncRelationshipsUseCase
    heartbeat_monitor: HeartbeatMonitor


def get_data_dir() -> Path:
    """Obtém o diretório base a partir da variável MITRARR_DATA_DIR."""
    raw = os.environ.get("MITRARR_DATA_DIR", "~/.mitrarr")
    return Path(raw).expanduser()


def build_container(base_dir: Path | None = None) -> AppContainer:
    """Cria todas as dependências concretas do sistema."""
    data_dir = base_dir or get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    nist_repo = JsonNistRepository(data_dir / "nists")
    rel_repo = JsonRelationshipRepository(data_dir / "relationships")
    gateway = LogFileFindFaceGateway(data_dir / "logs")
    heartbeat = HeartbeatMonitor(data_dir / "monitoring" / "heartbeats.json")

    return AppContainer(
        register_nist=RegisterNistUseCase(nist_repo),
        send_to_findface=SendToFindFaceUseCase(nist_repo, gateway),
        sync_relationships=SyncRelationshipsUseCase(rel_repo),
        heartbeat_monitor=heartbeat,
    )
