from flask import Blueprint, request, jsonify
import filetype
from io import BytesIO
from findface_multi.findface_multi import FindfaceConnection, FindfaceMulti, FindfaceException
import os
from funcoes import converter_card_para_pessoa

raiz_bp = Blueprint('raiz', __name__, url_prefix='/')

@raiz_bp.route('/', methods=['GET'])
def rais():
    return jsonify(mensagem="Olá Mundo!")
