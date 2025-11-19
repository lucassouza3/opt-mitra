from flask import Blueprint, request, jsonify
import filetype
from io import BytesIO
from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
import os
from funcoes import converter_card_para_pessoa
import json

pessoas_bp = Blueprint('pessoas', __name__, url_prefix='/pessoas')

@pessoas_bp.route('/', methods=['GET'])
def pessoas():

    # Define os parâmetros permitidos
    parametros_permitidos = ['nome', 'cpf', 'mae', 'pai', 'rnm', 'passaporte']

    # Captura todos os parâmetros passados na query string
    parametros_passados = request.args.keys()

    # Verifica se algum parâmetro passado não é permitido
    parametros_invalidos = [param for param in parametros_passados if param not in parametros_permitidos]
    
    if parametros_invalidos:
        return jsonify({"erro": f"Parâmetros desconhecidos: {', '.join(parametros_invalidos)}"}), 400

    # Extrai os parâmetros recebidos da query string
    parametros_recebidos = {}
    for param in parametros_permitidos:
        value = request.args.get(param)
        if value:
            # Substitui 'nome' por 'name'
            if param == 'nome':
                parametros_recebidos['name_contains'] = value
            else:
                parametros_recebidos[param] = value    

    # Retorna os parâmetros e valores recebidos
    # return jsonify(parametros_recebidos)

    usuario = os.environ["USUARIO_CONSULTA_FF"]
    senha = os.environ["SENHA_CONSULTA_FF"]

    try:
        with FindfaceConnection(base_url='https://findface2-mitrarr.ddns.net', username=usuario, password=senha) as ffcon:
            findface = FindfaceMulti(findface_connection=ffcon)

            cards = findface.get_human_cards(**parametros_recebidos)

            if cards:

                pessoas = [converter_card_para_pessoa(findface, x) for x in cards["results"]]

                return jsonify(mensagem=f"{len(pessoas)} pessoa(s) encontradas!", pessoas=pessoas, status=1), 200
            else:
                return jsonify(mensagem=f"Nenhuma pessoa encontrada.", pessoas=[], status=0), 404

    except FindfaceException as e:
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "Erro inesperado ao processar a solicitação."}), 500    
