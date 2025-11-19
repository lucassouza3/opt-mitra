"""Interfaces que definem os contratos entre o domínio e a infraestrutura."""

from .gateways import FindFaceGateway
from .repositories import NistRepository, RelationshipRepository

__all__ = ["FindFaceGateway", "NistRepository", "RelationshipRepository"]
