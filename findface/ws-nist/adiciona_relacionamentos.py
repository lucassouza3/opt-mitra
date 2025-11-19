from app import app
from database.models import db, Nist, BaseOrigem, BaseOrigemFindface, Findface, NistFindface, Log
from pathlib import Path
from nist_manager import obter_todas_as_novas_relacoes_nist_findface
import os


if __name__ == '__main__':

    root_dir = Path(__file__).parent / 'nists'

    with app.app_context() as context:        

        # Cria os novo relacionamentos NistFindface
        print(f"[adiciona_novos_relacionamentos] Criando novas relações NistFindface...")
        novas_relacoes = obter_todas_as_novas_relacoes_nist_findface()


    print(f"[adiciona_novos_relacionamentos] Finalizado.")