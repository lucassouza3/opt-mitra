from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
from mitra_toolkit.mitra_toolkit import MitraToolkit, MitraException
import os
import json
from datetime import datetime
import requests
import io


ff_url = os.environ["FINDFACE_URL"]
ff_user = os.environ["FINDFACE_USER"]
ff_password = os.environ["FINDFACE_PASSWORD"]

def log_message(message: str) -> str:

    print(f'{datetime.now().isoformat()} - {message}')


if __name__ == '__main__':

    with FindfaceConnection(base_url=ff_url, username=ff_user, password=ff_password) as ffcon:

        findface = FindfaceMulti(findface_connection=ffcon)
        mitra = MitraToolkit(findface=findface)

        source_photo = r'./foto.jpg'

        # Determine the type of source_photo and prepare it for the request
        if isinstance(source_photo, str):  # file path
            file_stream = open(source_photo, 'rb').read()
        elif isinstance(source_photo, bytes):  # bytes
            file_stream = source_photo
        elif isinstance(source_photo, io.BytesIO):  # io.BytesIO object
            file_stream
        else:
            raise TypeError(f"'source_photo' inválido. Aceitos string com o caminho do arquivo, bytes, or io.BytesIO.")
        
        log_message("Detectando de faces...")

        faces_with_quality = []

        detection = findface.detect(file_stream, face={})

        if detection:
            # Se mais de uma face foi encontrada na foto
            if len(detection["objects"]["face"]) > 0: 
                
                log_message(f'{len(detection["objects"]["face"])} face(s) encontrada(s) na foto.')
                
                # Seleciona as faces com qualidade de detecção
                for face_object in detection["objects"]["face"]:                    
                    if not face_object["low_quality"]:
                        faces_with_quality.append( {'face_object': face_object, 'content': file_stream} )
            else:
                raise MitraException('Nenhuma face encontrada na foto.')

        # Se não encontrou faces com qualidade, dispara uma exceção
        if len(faces_with_quality) == 0:
            raise MitraException('Nenhuma face com qualidade enncontrada na foto.')
        
        log_message(f'{len(faces_with_quality)} face(s) com qualidade encontrada(s) na foto.')

        cards_encontrados = []
        lista_cards_url = []
        # Para cada face com qualidade
        for face_with_quality in faces_with_quality:

            # Pesquisa no Findface cards com faces semelhantes
        
            # Cria um dicionário com os filtros de pesquisa
            card_filters = {}
            
            # Adiciona o detection id da mellhor foto como parâmetro da pesquisa
            card_filters["looks_like"] = f'detection:{face_with_quality["face_object"]["id"]}'

            log_message("Pesquisando cards...")
            # Pesquisa cards com faces semelhantes
            cards = findface.get_human_cards(**card_filters)["results"]
            if len(cards) > 0:
                cards_encontrados.extend(cards)
                log_message(f'{len(cards_encontrados)} cards encontrados.')

        # Busca as fotos
        for card in cards_encontrados:

            log_message(f'Buscando url da foto {card["looks_like"]["matched_object"]}...')
            
            face_object = findface.get_face_object_by_id(card["looks_like"]["matched_object"])

            log_message("Url recuperada.")

            log_message(f"Baixando foto do card {card['id']}...")

            response = requests.get(url=face_object["source_photo"], verify=False)

            if response.status_code in (200, 201):
                log_message("Foto baixada.")

            # Adiciona a url da foto ao card
            card["looks_like"]["matched_object_url"] = face_object["source_photo"]

        # return cards_encontrados
