from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from werkzeug.exceptions import BadRequest
from database.models import db, Nist
import os
import traceback
from NIST import NIST
from pathlib import Path
from database.models import Findface, BaseOrigem
from datetime import datetime
from io import BytesIO
from flask import current_app
from mitra_toolkit.functions import *
import hashlib
import sys
from config_app import APP_DIR


bp_upload_nist = Blueprint('bp_upload_nist', __name__)


@bp_upload_nist.route('/api/v1/upload-nist/', methods=['POST'])
def handle_nist():
    
    try:
        # Ensure there are files in the request
        if 'arquivo_nist' not in request.files:
            raise BadRequest("Nenhum arquivo enviado.")


        with current_app.app_context() as context:
            # Get the files list
            files = request.files.getlist('arquivo_nist')

            

            arquivos_ja_enviados = set()
            arquivos_recebidos = set()
            arquivos_rejeitados = []
            
            for file in files:

                print("[WS-NIST] Lendo arquivo", file.filename)
                # Valida o NIST
                # file = request.files.get(file, None)
                memory_file = BytesIO(file.read())

                filename = secure_filename(file.filename)

                try:
                    nist = NIST(memory_file.getvalue())
                except Exception as e:
                    rejeitado = {'arquivo': filename, 'motivo': 'Nist inválido.'}
                    if filename not in [x["arquivo"] for x in arquivos_rejeitados]:
                        arquivos_rejeitados.append(rejeitado)
                        continue

                nome_base_origem = nist.get_field('1.008')
                if not nome_base_origem:
                    rejeitado = {'arquivo': filename, 'motivo': 'Campo NIST "1.008" (Base de Origem) vazio.'}
                    if filename not in [x["arquivo"] for x in arquivos_rejeitados]:
                        arquivos_rejeitados.append(rejeitado)
                        continue
                
                nome_base_origem = formata_nome_base_origem(nome_base_origem)                    

                nome_pessoa = nist.get_field('2.030')
                if not nome_pessoa:
                    rejeitado = {'arquivo': filename, 'motivo': 'Campo "nome" (2.030) vazio.'}
                    if filename not in [x["arquivo"] for x in arquivos_rejeitados]:
                        arquivos_rejeitados.append(rejeitado)
                        continue

                # Verifica se a base de origem existe no banco de dados
                base_origem = BaseOrigem.query.filter(BaseOrigem.no_base_origem==nome_base_origem).first()
                if not base_origem:
                    rejeitado = {'arquivo': filename, 'motivo': f'Base de Origem do NIST "{nome_base_origem}" desconhecida. Contate o administrador <leonardo.lad@pf.gov.br>.'}
                    if filename not in [x["arquivo"] for x in arquivos_rejeitados]:
                        arquivos_rejeitados.append(rejeitado)
                        continue
                
                nist_relative_filepath = 'nists/' + str(nome_base_origem).lower() + '/' + datetime.now().strftime('%Y-%m-%d') + f'/{filename}'
                nist_full_filepath = APP_DIR / nist_relative_filepath
                nist_full_dir = nist_full_filepath.parent

                os.makedirs(nist_full_dir, exist_ok=True)

                # Patch necessário porque o hash md5 direto do arquivo em memória não estava 
                # batendo com o hash md5 gerado na inclusão do Nist no banco
                temp_file = 'temp/' + hashlib.md5(memory_file.getvalue()).hexdigest() + '.tmp'
                nist.write(temp_file)                
                with open(temp_file, 'rb') as fb:
                    nist_content = fb.read()
                    md5_hash = hashlib.md5(nist_content).hexdigest()
                os.remove(temp_file)

                # Verifica se o Nist já foi enviado pelo seu hash md5                
                # md5_hash = hashlib.md5(memory_file.getvalue()).hexdigest()
                
                # print('[WS-NIST] hash', md5_hash, len(memory_file.getvalue()), 'bytes')

                reje = [x["arquivo"] for x in arquivos_rejeitados]
                # print('[WS-NIST] rejeitados', reje)

                if Nist.query.filter(Nist.md5_hash==md5_hash).first() or nist_full_filepath.exists():
                    if filename not in [x["arquivo"] for x in arquivos_rejeitados]:
                        # arquivos_ja_enviados.add(filename)
                        arquivos_ja_enviados.add(str(nist_full_filepath))                        
                    # print(f'[WS-NIST] Arquivo já enviado {nist_full_filepath}')
                else:
                    if filename not in [x["arquivo"] for x in arquivos_rejeitados]:
                        arquivos_recebidos.add(str(nist_full_filepath))
                        nist.write(str(nist_full_filepath))
                        # print(f'[WS-NIST] Arquivo recebido {nist_full_filepath}')

            return jsonify(recebidos=list(arquivos_recebidos), existentes=list(arquivos_ja_enviados), rejeitados=list(arquivos_rejeitados))

    except:
        return jsonify(message=traceback.format_exc()), 500

