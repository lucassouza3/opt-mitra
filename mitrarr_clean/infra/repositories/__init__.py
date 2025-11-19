"""Repositórios concretos utilizados na camada de infraestrutura."""

from .nist_json import JsonNistRepository
from .relationships_json import JsonRelationshipRepository

__all__ = ["JsonNistRepository", "JsonRelationshipRepository"]
