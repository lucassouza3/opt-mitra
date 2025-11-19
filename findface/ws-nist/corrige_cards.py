from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
import os
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import threading
import mylogger
from datetime import datetime


def exclui_card(findface: FindfaceMulti, card: dict, arquivo_conf_lista: str) -> None:
    """
    Exclui um cartão do sistema FindFace.

    Parameters:
    - findface (FindfaceMulti): Conexão com o sistema FindFace.
    - card (dict): Dicionário com informações do cartão.

    Returns:
    - None
    """
    if not isinstance(findface, FindfaceMulti):
        raise TypeError("findface deve ser uma instância de FindfaceMulti.")
    if not isinstance(card, dict):
        raise TypeError("card deve ser um dicionário.")

    try:
        findface.delete_human_card(card["id"])
        with log_lock:
            logger.info(f"Card #{card['id']} excluído. Lista: {card['watch_lists']}, Sexo: {card['meta']['sexo']}, Nascimento: {card['meta']['data_nascimento']}")
    except Exception as e:
        with log_lock:
            logger.error(f"{str(e)}")

    # Salva a data da ultima atualização
    data_criacao = card["created_date"]
    with txt_lock:
        with open(arquivo_conf_lista, 'w') as wf:
            wf.write(data_criacao)


def imprime_card(findface: FindfaceMulti, card: dict) -> None:
    """
    Imprime informações de um cartão no log.

    Parameters:
    - findface (FindfaceMulti): Conexão com o sistema FindFace.
    - card (dict): Dicionário com informações do cartão.

    Returns:
    - None
    """
    if not isinstance(findface, FindfaceMulti):
        raise TypeError("findface deve ser uma instância de FindfaceMulti.")
    if not isinstance(card, dict):
        raise TypeError("card deve ser um dicionário.")

    logger.info(f"Card #{card['id']}, Listas: {card['watch_lists']}")


def main() -> None:
    """
    Função principal para processar e excluir cartões em paralelo do sistema FindFace.
    """
    FINDFACE_URL = os.environ["FINDFACE_URL"]
    FINDFACE_USER = os.environ["FINDFACE_USER"]
    FINDFACE_PASSWORD = os.environ["FINDFACE_PASSWORD"]

    with FindfaceConnection(base_url=FINDFACE_URL, username=FINDFACE_USER, password=FINDFACE_PASSWORD, uuid="corrige_card.py") as ffcon:
        findface = FindfaceMulti(findface_connection=ffcon)

        listas = ["MA/CIVIL"]

        for lista in listas:
            prefixo_lista = lista.replace('/', '-')
            arquivo_conf_lista = "corrige_card_" + prefixo_lista.lower() + '.txt'

            # Data de criação inicial
            data_criacao = "2020-01-01T00:00:0.000000Z"
            if os.path.exists(arquivo_conf_lista):
                with open(arquivo_conf_lista) as f:
                    data_criacao = f.read()
            
            # Obtém o ID d lista no Findface
            id_lista = findface.get_watch_list_id_by_name(lista)

            while True:               

                cards = findface.get_human_cards(
                    watch_lists=[id_lista],
                    created_date_gt=data_criacao,
                    has_face_objects=True,
                    ordering='created_date',
                    limit=400
                )

                if cards["results"]:                    
                    # Atualiza a data de criação
                    cards["results"][-1]["created_date"]
                    
                    cards_selecionados = [x for x in cards["results"] if x["meta"]["sexo"] == 'F' or ( datetime.strptime(x["meta"]["data_nascimento"], r"%Y-%m-%d") >= datetime(2015, 1, 1) )]

                    # Selecion os cards para exclusão. Critérios:
                    # 1 - Todos do sexo feminino
                    # 2 - Data de nascimento > 2015
                    if cards_selecionados:                        
                        # print(json.dumps(cards_selecionados, indent=4))                    
                        # exit(-1)

                        # Agora com 4 workers fixos
                        with ThreadPoolExecutor(max_workers=4) as executor:
                            futures = [
                                executor.submit(exclui_card, findface, card, arquivo_conf_lista)
                                for card in cards_selecionados
                            ]
                            for future in futures:
                                future.result()
                else:
                    break


if __name__ == '__main__':

    log_file = Path(__file__).parent / 'corrige_card.log'
    # Logger configurado
    logger = mylogger.configurar_logger(str(log_file))
    # Lock global para sincronização do logger    
    log_lock = threading.Lock()
    # Lock global para gravação no arquivo TXT de controle de data da última leitura
    txt_lock = threading.Lock()

    main()
