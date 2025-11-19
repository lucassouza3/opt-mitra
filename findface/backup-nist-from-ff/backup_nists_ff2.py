from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
from NIST3.functions_mitra_toolkit import *
import os
import json
import requests
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor


FINDFACE_URL = os.environ["FINDFACE_URL"]
FINDFACE_USER = os.environ["FINDFACE_USER"]
FINDFACE_PASSWORD = os.environ["FINDFACE_PASSWORD"]


def obter_caminho_arquivo_nist(card, nome_lista):

    backup_dir = Path(__file__).parent / f"backup_nists"    
    prefixo = nome_lista.lower().replace('/', '_')
    filepath = backup_dir / f"{nome_lista.lower()}/{prefixo}_{card['id']}.nst"

    return filepath


def gera_nist(card: dict, faces_bin: bytes, nome_lista: str) -> None:

    nome = formata_nome(card["name"])
    rg = formata_documento(card["meta"]["documento"])
    cpf = validate_cpf(card["meta"]["cpf"])

    new_nist = NIST()
    new_nist.add_Type01()
    new_nist.add_Type02()
    
    if card["meta"]["data_nascimento"]:
        if 'T' in card["meta"]["data_nascimento"]:
            data_nascimento = card["meta"]["data_nascimento"].split('T')[0]
        else:
            data_nascimento = card["meta"]["data_nascimento"]
            
        data_nascimento_formatada = formata_data_nascimento(data_nascimento, r"%Y%m%d")
        new_nist.set_field('2.035', data_nascimento_formatada, idc=0)  # Data de nascimento

    new_nist.set_field('1.008', nome_lista, idc=0)  # Base de Origem
    new_nist.set_field('2.030', nome, idc=0)  # Nome    
    # new_nist.set_field('2.037', 'Smyrna/GA', idc=0)  # Cidade de nascimento
    new_nist.set_field('2.038', formata_nacionalidade(card["meta"]["nacionalidade"]), idc=0)  # País de nascimento
    # new_nist.set_field('2.039', '2', idc=0)  # Sexo 1|M-Masculino, 2|F-Feminino, ?|O-Outros
    new_nist.set_field('2.201', formata_nome(card["meta"]["pai"]), idc=0)  # Pai
    new_nist.set_field('2.202', formata_nome(card["meta"]["mae"]), idc=0)  # Mae
    new_nist.set_field('2.211', rg, idc=0)  # Identidade
    new_nist.set_field('2.212', cpf, idc=0),  # CPF
    # new_nist.set_field('2.213', '', idc=0)  # Titulo de eleitor
    # new_nist.set_field('2.214', '', idc=0)  # CNH
    # new_nist.set_field('2.224', 'JULIA ROBERTS')  # Nome social

    # Faces
    new_nist.add_ntype(10)
    for index, face in enumerate(faces_bin, start=1):
        new_nist.set_field('10.999', face, idc=index)


    filepath = obter_caminho_arquivo_nist(card=card, nome_lista=nome_lista)
        
    # Cria o diretório e seus pais, se necessário
    os.makedirs(Path(filepath).parent, exist_ok=True)

    new_nist.write(filepath)

    print(f"Arquivo criado: {filepath}.")


def backup_card(findface: FindfaceMulti, card: dict, nome_lista: str) -> None:
    
    # Verifica se o arquivo já existe no destino. Se existir, sai da função
    caminho_arquivo_nist = obter_caminho_arquivo_nist(card=card, nome_lista=lista)
    if os.path.exists(caminho_arquivo_nist):
        print(f"Arquivo já existe.", caminho_arquivo_nist)
        return    

    face_objects = findface.get_face_objects(card=card["id"])
    faces_bin = []
    for face_object in face_objects["results"]:
        response = requests.get(face_object["source_photo"], verify=False)
        if response.status_code == 200:
            faces_bin.append(response.content)

    gera_nist(card, faces_bin=faces_bin, nome_lista=lista)


if __name__ == '__main__':

    with FindfaceConnection(base_url=FINDFACE_URL, username=FINDFACE_USER, password=FINDFACE_PASSWORD, uuid="backup_nist_ff2.py") as ffcon:
        findface = FindfaceMulti(findface_connection=ffcon)

        listas = ["PF/GCAP-RR"]
        
        for lista in listas:

            prefixo_lista = lista.replace('/','_')
            arquivo_conf_lista = prefixo_lista.lower() + '.txt'

            # Seta a data de criação do último card lido da lista
            data_criacao = "2020-01-01T00:00:0.000000Z"  # Data default
            if os.path.exists(arquivo_conf_lista):
                with open(arquivo_conf_lista) as f:
                    # data_criacao = f.read().splitlines()[0]
                    data_criacao = f.read()

            for i in range(9000000):  # Loop virtualmente infinito para poder limitar o número de retornos a cada loop

                # print("data criação", data_criacao)

                id_lista = findface.get_watch_list_id_by_name(lista)

                cards = findface.get_human_cards(watch_lists=[id_lista], created_date_gt=data_criacao, has_face_objects=True, ordering='created_date', limit=100)

                if cards["results"]:
                    # Atualiza da data de criação do último card lido
                    data_criacao = cards["results"][-1]["created_date"]

                    # Execução em paralelo para todos os cards
                    with ThreadPoolExecutor() as executor:
                        # Submete todas as tarefas de uma vez
                        futures = [executor.submit(backup_card, findface, card, lista) for card in cards["results"]]
                        
                        # Aguarda a conclusão de todas as tarefas
                        for future in futures:
                            future.result()  # Bloqueia até que cada tarefa seja concluída

                    # Após a conclusão de todas as tarefas, escreve no arquivo
                    with open(arquivo_conf_lista, 'w') as wf:
                        wf.write(data_criacao)
                else:
                    break
