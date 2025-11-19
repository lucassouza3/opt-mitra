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
import traceback



def envia_nist_findface_paralelo(nist):
    with app.app_context() as context:
        return envia_nist_para_findface(nist)


def apaga_card(card_id):
    FINDFACE_USER = os.environ["FINDFACE_USER"]
    FINDFACE_PASSWORD = os.environ["FINDFACE_PASSWORD"]
    FINDFACE_HOST = os.environ["FINDFACE_HOST"]
    url_base = FINDFACE_HOST
    with FindfaceConnection(base_url=url_base, username=FINDFACE_USER, password=FINDFACE_PASSWORD) as findface_connection:
        findface_multi = FindfaceMulti(findface_connection)

        if findface_multi.delete_human_card(card_id=card_id):
            print(f"Card '{card_id}' excluído!")
        else:
            print(f"Erro na exclusão do card {card_id}")


def exclui_arquivo(filepath):
    # Excluindo o arquivo
    try:
        os.remove(filepath)
        print(f'Arquivo "{filepath}" excluído com sucesso.')
    except FileNotFoundError:
        print(f'O arquivo "{filepath}" não foi encontrado.')
    except PermissionError:
        print(f'Você não tem permissão para excluir o arquivo "{filepath}".')
    except Exception as e:
        print(f'Ocorreu um erro ao tentar excluir o arquivo: {e}')    


if __name__ == '__main__':

    arquivo = Path(__file__).parent / 'corrige_detran-antigo.out'

    with open(arquivo, 'rt') as f:
        caminhos = f.read().splitlines()

    caminhos = set(caminhos)
    
    with app.app_context() as context:
        
        for caminho in caminhos:
            print(f'Pesquisando caminho {caminho}...')
            nist = Nist.query.filter(Nist.uri_nist == caminho).first()

            if nist:
                nist_findface = NistFindface.query.filter(NistFindface.id_nist == nist.id_nist).first()
                if nist_findface:

                    if nist_findface.card_id:
                        # Exclui do Findface
                        try:
                            apaga_card(nist_findface.card_id)
                            print(f"Card {nist_findface.card_id} excluído!")
                        except Exception as e:
                            print(traceback.format_exc())

                    # Remove o Nist do banco
                    nist_id = nist.id_nist
                    db.session.delete(nist)
                    db.session.commit()
                    print(f"Nist #{nist_id} excluído do banco.")

            # Exclui o arquivo do sistema
            if os.path.exists(caminho):
                os.remove(caminho)
                print("Arquivo excluído", caminho)
            else:
                print("Arquivo não encontrado no disco", caminho)

    print(f"Finalizado.")