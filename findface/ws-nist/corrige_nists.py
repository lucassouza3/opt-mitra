from config_app import *
from database.models import db, Nist
from app import app
from datetime import datetime
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path



if __name__ == '__main__':

    with app.app_context() as context:

        diretorio_base = Path('/mnt/mitra/')
        diretorio_nists = Path('nists/rr/civil-antigo/')

        arquivos = [x for x in diretorio_nists.iterdir() if x.is_file()]

        for arquivo_nist in arquivos:
            subdiretorio = str(arquivo_nist.stem)[-2:]
            if not subdiretorio.isdigit():
                subdiretorio = '00'

            caminho_completo = diretorio_base / diretorio_nists

            caminho_completo_arquivo = caminho_completo / arquivo_nist.name
            
            # Diretório destino
            # diretorio_destino = diretorio_nists / subdiretorio  # Windows
            diretorio_destino = caminho_completo / subdiretorio  # Posix           

            # Crie o diretório destino se ele não existir
            diretorio_destino.mkdir(parents=True, exist_ok=True)

            # Caminho completo do arquivo de destino
            novo_arquivo = diretorio_destino / arquivo_nist.name

            nist = Nist.query.filter(Nist.uri_nist==str(caminho_completo_arquivo)).first()
            if nist:
                nist.uri_nist = str(novo_arquivo)
                db.session.commit()
                print(f"URI Nist atualizado: {nist.uri_nist}")
            else:
                print(f"URI Nist não encontrado: {caminho_completo_arquivo}")

            # Move o arquivo A para o diretório Y
            arquivo_nist.rename(novo_arquivo)
            print(f"Arquivo movido de '{str(caminho_completo_arquivo)}' para '{str(novo_arquivo)}'")

        
