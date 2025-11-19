from flask import Blueprint, request, jsonify
import filetype
from io import BytesIO
from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
import os
from funcoes import converter_card_para_pessoa

reconhecimento_facial_bp = Blueprint('reconhecimento-facial', __name__, url_prefix='/reconhecimento-facial')

@reconhecimento_facial_bp.route('/', methods=['POST'])
def foto():
    # Verifica se o arquivo foi enviado com o nome de campo 'arquivo'
    if 'arquivo' not in request.files:
        # return jsonify({'error': 'Nenhum arquivo foi enviado.'}), 400
        return jsonify(mensagem="Nenhum arquivo foi enviado.", pessoas=[], status=0), 400

    file = request.files['arquivo']

    # Verifica se o nome do arquivo é válido
    if file.filename == '':        
        # return jsonify({'error': 'Nenhum arquivo selecionado.'}), 400
        return jsonify(mensagem="Nenhum arquivo selecionado.", pessoas=[], status=0), 400

    # Lê o conteúdo do arquivo em memória
    file_bytes = BytesIO(file.read())

    # Verifica o mime-type do arquivo usando filetype
    kind = filetype.guess(file_bytes)

    # Verifica se o arquivo é uma imagem válida
    if kind is None or kind.mime.split('/')[0] != 'image':
        # return jsonify({'error': 'Arquivo enviado não é uma imagem válida.'}), 400
        return jsonify(mensagem="Arquivo enviado não é uma imagem válida.", pessoas=[], status=0), 400

    # Se o arquivo for uma imagem válida, responde com sucesso
    # return jsonify({'message': 'Arquivo recebido é uma imagem válida.'}), 200

    usuario = os.environ["USUARIO_CONSULTA_FF"]
    senha = os.environ["SENHA_CONSULTA_FF"]

    try:
        with FindfaceConnection(base_url='https://findface2-mitrarr.ddns.net', username=usuario, password=senha) as ffcon:
            findface = FindfaceMulti(findface_connection=ffcon)

            pessoas_encontradas = reconhecimento_facial(findface, file_bytes)

            if pessoas_encontradas:
                mensagem = f"{len(pessoas_encontradas)} pessoa(s) encontradas!"
                return jsonify(mensagem=mensagem, pessoas=pessoas_encontradas, status=1), 200
            else:
                return jsonify(message="Nenhum cadastro encontrado para face pesquisada.", pessoas=[], status=0), 200

    except FindfaceException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500    


def reconhecimento_facial(findface, source_photo:str|bytes|BytesIO):

    # Determine the type of source_photo and prepare it for the request
    if isinstance(source_photo, str):  # file path
        file_stream = open(source_photo, 'rb').read()
    elif isinstance(source_photo, bytes):  # bytes
        file_stream = source_photo
    elif isinstance(source_photo, BytesIO):  # io.BytesIO object
        file_stream = source_photo.getvalue()
    else:
        raise TypeError(f"[reconhecimento_facial] 'source_photo' inválido. Aceitos string com o caminho do arquivo, bytes, or io.BytesIO.")

    if len(file_stream) == 0:
        raise ValueError(f'[reconhecimento_facial] Arquivo foto vazio.')

    faces_with_quality = []

    detection = findface.detect(file_stream, face={})
    if detection:
        # Se mais de uma face foi encontrada na foto
        if len(detection["objects"]["face"]) > 0: 
            print(f'[reconhecimento_facial] {len(detection["objects"]["face"])} face(s) encontrada(s) na foto.')
            # Seleciona as faces com qualidade de detecção
            for face_object in detection["objects"]["face"]:                    
                if not face_object["low_quality"]:
                    faces_with_quality.append( {'face_object': face_object, 'content': file_stream} )
        else:
            raise MitraException('Nenhuma face encontrada na foto.')

    # Se não encontrou faces com qualidade, dispara uma exceção
    if len(faces_with_quality) == 0:
        raise MitraException('Nenhuma face com qualidade enncontrada na foto.')
    
    print(f'[reconhecimento_facial] {len(faces_with_quality)} face(s) com qualidade encontrada(s) na foto.')

    cards_encontrados = []
    lista_cards_url = []
    # Para cada face com qualidade
    for face_with_quality in faces_with_quality:

        # Pesquisa no Findface cards com faces semelhantes
    
        # Cria um dicionário com os filtros de pesquisa
        card_filters = {}
        
        # Adiciona o detection id da mellhor foto como parâmetro da pesquisa
        card_filters["looks_like"] = f'detection:{face_with_quality["face_object"]["id"]}'

        # Pesquisa cards com faces semelhantes
        cards = findface.get_human_cards(**card_filters)["results"]
        if len(cards) > 0:
            cards_encontrados.extend(cards)

    # Busca as fotos
    for card in cards_encontrados:
        face_object = findface.get_face_object_by_id(card["looks_like"]["matched_object"])

        # Adiciona a url da foto ao card
        card["looks_like"]["matched_object_url"] = face_object["source_photo"]

    # return cards_encontrados

    return [converter_card_para_pessoa(findface, x) for x in cards_encontrados]
