from app import app
from database.models import db, Nist, BaseOrigem, BaseOrigemFindface, Findface, NistFindface, Log
from pathlib import Path
from nist_manager import envia_nist_para_findface, obtem_todos_os_nists_com_findface_mas_sem_cardid
from manual_upload import envia_nist_findface_paralelo, adiciona_relacao_nist_findface_em_paralelo
from threader import Threader
from sqlalchemy.orm import aliased
from sqlalchemy import and_, select
import sys
import os


def add_novos_findfaces():
    """
    Função que encontra Findfaces sem Nist correspondente (novo findface), 
    depois enconra todos os NISTs relacionados ao novo findface por meio da base de origem do Nist
    e cria as relações NistFindface
    """
    novos_findfaces = []        
    # Encontra novos Findfaces
    findfaces = Findface.query.all()
    for findface in findfaces:
        if NistFindface.query.filter(NistFindface.id_findface == findface.id_findface, NistFindface.id_nist.isnot(None)).first():
            pass
        else:
            # Verifica se já existe Base de Origem relacionada com os Findfaces encontrados
            if BaseOrigemFindface.query.filter(BaseOrigemFindface.id_findface==findface.id_findface).first():
                # print(f'[novos_findfaces] Base de origem encontrada para Findface #{findface.id_findface}')
                novos_findfaces.append(findface)
            else:
                pass
                # print(f'[novos_findfaces] Nenhuma Base de Origem associada ao Findface #{findface.id_findface}')

    # Encontra os NISTs que possuem bases de origem relacionadas ao Findface criado
    if novos_findfaces:
        print(f'[novos_findfaces] Novos Findfaces encontrados:', [x.no_findface for x in novos_findfaces])
        lista_novos_nists = []
        for findface in novos_findfaces:
            # print('novo Findface(s)', findface, findface.base_origens)
            lista_novas_relacoes_nist_findface = []
            for base_origem in findface.base_origens:
                for nist in base_origem.nists:
                    if nist not in lista_novos_nists:
                        lista_novos_nists.append(nist)
                        lista_novas_relacoes_nist_findface.append(NistFindface(id_nist=nist.id_nist, id_findface=findface.id_findface))

            # Cadastra as novas relações criadas para os NISTs do novo Findface
            print(f"[novos_findfaces] {len(lista_novas_relacoes_nist_findface)} novas relações com o '{findface.no_findface}'. Salvando no banco...")
            th_relacao = Threader(lista_novas_relacoes_nist_findface, adiciona_relacao_nist_findface_em_paralelo)
            print(f'[novos_findfaces] Concluído.')
 
        return lista_novos_nists

    else:
        print(f'[novos_findfaces] Nenhum novo Findface encontrado.')


if __name__ == '__main__':
    
    with app.app_context() as context:
        
        lista_novos_nists = add_novos_findfaces()

        if lista_novos_nists:

            # Em paralelo, envia novos NISTs para o(s) Findface(s) relacionados           
            print(f"[novos_findfaces] Enviando para o(s) Findface(s)...")
            th_cards = Threader(lista_novos_nists, envia_nist_findface_paralelo)

        print(f"[novos_findfaces] Finalizdo.")
