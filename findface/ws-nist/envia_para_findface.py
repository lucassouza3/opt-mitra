from app import app
from database.models import db, Nist, BaseOrigem, BaseOrigemFindface, Findface, NistFindface, Log
from pathlib import Path
from nist_manager import envia_nist_para_findface, obtem_todos_os_nists_com_findface_mas_sem_cardid
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy.orm import aliased
from sqlalchemy import and_, select
import sys
import os


def envia_nist_findface_paralelo(nist):
    with app.app_context() as context:
        return envia_nist_para_findface(nist)


if __name__ == '__main__':

    root_dir = Path(__file__).parent / 'nists'
    with app.app_context() as context:

        offset = 0
        limit = 100 * os.cpu_count()
        while True:
            # Obtem a lista dos NISTs que estão sem card_id
            lista_nists_sem_findface = obtem_todos_os_nists_com_findface_mas_sem_cardid(limit=limit, offset=offset)
            if lista_nists_sem_findface:
                MAX_WORKERS = 4
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    result = executor.map(envia_nist_findface_paralelo, lista_nists_sem_findface)
                    offset += limit
            else:
                break

    print(f"[envia_para_findface] Finalizado.")