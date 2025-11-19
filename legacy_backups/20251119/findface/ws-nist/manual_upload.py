from app import app
from database.models import db, Nist, BaseOrigem, BaseOrigemFindface, Findface, NistFindface, Log
from pathlib import Path
from nist_manager import envia_nist_para_findface, add_nist, obter_caminho_absoluto_nist
from nist_manager import add_novas_relacoes_por_nist, add_nist_to_db_by_uri, obtem_todos_os_nists_com_findface_mas_sem_cardid
from nist_manager import obter_todas_as_novas_relacoes_nist_findface
from threader import Threader
from sqlalchemy.orm import aliased
from sqlalchemy import and_, select
import sys
import os


def get_nists_in_files(root_dir):
    if isinstance(root_dir, str):
        if Path(root_dir).is_symlink():
            root_dir = Path(root_dir).resolve()  # Resolve to handle symbolic links
    elif not isinstance(root_dir, Path):
        raise TypeError(f'Invalid type {type(root_dir)} for "root_dir". Expected <class str> or <class "Path">.')

    nst_files = []
    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=True):  # followlinks=True to follow symlinks
        for filename in filenames:
            if filename.endswith('.nst'):
                nst_files.append(str(Path(dirpath) / filename))

    return nst_files


def get_nists_in_database():
    with app.app_context() as context:
        nists = Nist.query.all()
        lista_caminhos_nist = [obter_caminho_absoluto_nist(x.uri_nist) for x in nists]

        return lista_caminhos_nist


def obter_arquivos_nist_com_erro():
    with app.app_context() as context:
        nists_com_erro = Log.query.filter_by(cd_tipo_log = 18).all()
        nist_com_erro_caminho_absoluto = [obter_caminho_absoluto_nist(x.ds_log) for x in nists_com_erro]
        return nist_com_erro_caminho_absoluto


def adiciona_nist_em_paralelo(nist_filepath: str) -> None:

    with app.app_context() as context:
        novo_nist = add_nist_to_db_by_uri(nist_filepath)
        if novo_nist:
            return novo_nist


def adiciona_relacao_nist_findface_em_paralelo(relacao_nist_findface: NistFindface) -> NistFindface:
    with app.app_context() as context:

        db.session.add(relacao_nist_findface)
        db.session.commit()

        return relacao_nist_findface


def envia_nist_findface_paralelo(nist):
    with app.app_context() as context:
        return envia_nist_para_findface(nist)


if __name__ == '__main__':

    root_dir = Path(__file__).parent / 'nists'

    # Obtem os NISTs salvos no disco
    print(f'[manual_upload] Lendo NISTs no diretorio nists/...')
    nist_in_files = get_nists_in_files(str(root_dir))
    print(f'[manual_upload] {len(nist_in_files)} arquivos NIST encontrados.')

    # Obtem os NISTs contidos no banco de dados
    print(f'[manual_upload] Lendo NISTs banco de dados...')
    nist_in_database = get_nists_in_database()
    print(f'[manual_upload] {len(nist_in_database)} NISTs encontrados no banco de dados.')

    # Obtem os arquivos NIST com error para ignorar
    nists_com_erro = obter_arquivos_nist_com_erro()    
    print(f'[manual_upload] {len(nists_com_erro)} NISTs com erro encontrados.')

    # Subtrai da lista de NISTs do disco as listas de NISTs do banco de dados e NISTs com erro
    print(f'[manual_upload] Comparando NISTs do diretorio com os do banco de dados...')
    novos_uris = list(set(nist_in_files) - set(nist_in_database) - set(nists_com_erro))

    # O resultado é a lista de novos NISTs para inclusão no banco
    print(f'[manual_upload] {len(novos_uris)} novo(s) arquivo(s) NIST para inclusão no banco.')

    with app.app_context() as context:
        if novos_uris:
            # Em paralelo, cadastra os novos NISTs no banco
            # threads = Threader(novos_uris, add_nist, workers=24)

            print(f"[manual_upload] Lendo novos Nists e adicionando no banco...")
            # Em paralelo, salva os Nists no banco e cria seus relacionamentos com o(s) Findface(s)
            th_nists = Threader(novos_uris, adiciona_nist_em_paralelo)
            print(f"[manual_upload] {len(th_nists.return_list)} Nists adicionados com sucesso!")        
        
        # Cria os novo relacionamentos NistFindface
        print(f"[manual_upload] Obtendo novas relações NistFindface...")
        novas_relacoes_nist_findface = obter_todas_as_novas_relacoes_nist_findface()
        print(f"[manual_upload] {len(novas_relacoes_nist_findface)} novas relações encontradas.")
                
        # Obtem a lista dos NISTs que estão sem card_id
        lista_nists_sem_findface = obtem_todos_os_nists_com_findface_mas_sem_cardid()
        print(f"[manual_upload] {len(lista_nists_sem_findface)} NISTs sem card_id encontrados. Enviando para o(s) Findface(s)...")
        th_cards = Threader(lista_nists_sem_findface, envia_nist_findface_paralelo, workers=24)

    print(f"[manual_upload] Finalizado.")