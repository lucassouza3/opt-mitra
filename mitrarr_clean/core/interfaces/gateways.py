"""Gateways responsáveis por integrar com serviços externos."""

from __future__ import annotations

from typing import Protocol, Sequence

from core.entities import NistFile


class FindFaceGateway(Protocol):
    """Contrato para qualquer conector que envie dados para o FindFace."""

    def send_nists(self, nists: Sequence[NistFile]) -> None:
        """
        Envia uma sequência de registros para o FindFace.

        :param nists: coleção ordenada de registros normalizados.
        """

