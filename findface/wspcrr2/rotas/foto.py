from flask import Blueprint, request, jsonify, send_file
import filetype
from io import BytesIO
from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
import os
import requests


foto_bp = Blueprint('foto', __name__, url_prefix='/pessoas/foto')

@foto_bp.route('/<object_id>', methods=['GET'])
def foto(object_id):

    usuario = os.environ["USUARIO_CONSULTA_FF"]
    senha = os.environ["SENHA_CONSULTA_FF"]

    try:

        with FindfaceConnection(base_url='https://findface2-mitrarr.ddns.net', username=usuario, password=senha) as ffcon:
            findface = FindfaceMulti(findface_connection=ffcon)

            face_object = findface.get_face_object_by_id(int(object_id))

            if face_object:

                source_photo = face_object["source_photo"]
                source_photo_name = face_object["source_photo_name"]

                response = requests.get(url=source_photo, verify=False)
                if response.status_code in (200, 201):
                    foto_bytes = response.content

                    # Converte os bytes em um objeto BytesIO
                    foto_stream = BytesIO(foto_bytes)

                    # Retorna a imagem como uma resposta binária
                    return send_file(foto_stream, mimetype='image/jpeg', as_attachment=True, download_name=f"{object_id}.jpg")
                else:
                    return jsonify(mensagem=response.text)

            else:
                return jsonify(mensagem=f"Nenhuma foto encontrada para o objeto '{object_id}'.")

    except FindfaceException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500