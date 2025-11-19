from app import app
from database.models import db, Nist, BaseOrigem, BaseOrigemFindface, Findface, NistFindface, Log
from pathlib import Path
from nist_manager import envia_nist_para_findface, obtem_todos_os_nists_com_findface_mas_sem_cardid
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import aliased
from sqlalchemy import and_, select
import sys
import os
from findface_multi.findface_multi import FindfaceConnection, FindfaceException, FindfaceMulti


def obter_primeiro_parametro() -> int:
    """
    Obtém o primeiro parâmetro da linha de comando e verifica se é um número inteiro.

    Retorna:
        int: O número inteiro passado como argumento.

    Lança:
        ValueError: Se nenhum parâmetro for informado.
        ValueError: Se mais de um parâmetro for informado.
        TypeError: Se o parâmetro informado não for um número inteiro.
    """
    argumentos = sys.argv[1:]  # Ignora o nome do script

    # Verifica se há exatamente um argumento
    if not argumentos:
        raise ValueError("Erro: Nenhum parâmetro foi informado.")
    if len(argumentos) > 1:
        raise ValueError("Erro: Mais de um parâmetro foi informado.")

    # Verifica se o argumento é um número inteiro
    try:
        return int(argumentos[0])
    except ValueError:
        raise TypeError("Erro: O parâmetro informado não é um número inteiro.")


def envia_nist_findface_paralelo(nist):
    with app.app_context() as context:
        return envia_nist_para_findface(nist, carga_inicial=True)

if __name__ == '__main__':

    root_dir = Path(__file__).parent / 'nists'
    with app.app_context() as context:

        # Obrigatório informar o ID da base de origem da carga inicial
        BASE_ORIGEM_ID = obter_primeiro_parametro()

        if not BaseOrigem.query.filter(BaseOrigem.id_base_origem == BASE_ORIGEM_ID).first():
            raise ValueError(f"Base de origem #{BASE_ORIGEM_ID} inexistente.")

        offset = 0
        limit = 100 * os.cpu_count()
        while True:
            # Obtem a lista dos NISTs que estão sem card_id
            lista_nists_sem_findface = obtem_todos_os_nists_com_findface_mas_sem_cardid(limit=limit, offset=offset, base_origem_id=BASE_ORIGEM_ID)
            if lista_nists_sem_findface:
                MAX_WORKERS = os.cpu_count()
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    result = executor.map(envia_nist_findface_paralelo, lista_nists_sem_findface)
                    offset += limit
            else:
                break

    print(f"[envia_para_findface] Finalizado.")