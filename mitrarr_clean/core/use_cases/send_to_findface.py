"""Caso de uso que envia registros pendentes ao FindFace."""

from __future__ import annotations

from core.exceptions import UseCaseError
from core.interfaces import FindFaceGateway, NistRepository


class SendToFindFaceUseCase:
    """Orquestra o envio de registros pendentes ao serviço FindFace."""

    def __init__(self, repository: NistRepository, gateway: FindFaceGateway) -> None:
        """Inicializa o caso de uso com as dependências necessárias."""
        self._repository = repository
        self._gateway = gateway

    def execute(self, batch_size: int) -> int:
        """
        Envia um lote de registros.

        :param batch_size: quantidade máxima de itens por execução.
        :return: número de registros enviados com sucesso.
        """
        if batch_size <= 0:
            raise ValueError("batch_size deve ser positivo.")

        pending = list(self._repository.get_pending(batch_size))
        if not pending:
            return 0

        try:
            self._gateway.send_nists(pending)
        except Exception as exc:  # pragma: no cover
            raise UseCaseError("Falha ao enviar dados para o FindFace.") from exc

        try:
            self._repository.mark_as_sent([item.identifier for item in pending])
        except Exception as exc:  # pragma: no cover
            raise UseCaseError("Falha ao atualizar status após envio ao FindFace.") from exc
        return len(pending)
