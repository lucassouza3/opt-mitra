from idnetrr import wscivil, wsPolicia
from NIST import NIST
from functions import *
from pathlib import Path
from datetime import datetime
from threader import Threader
import traceback
import os
from concurrent.futures import ThreadPoolExecutor
import base64
import json
from idnetrr.idnetrr import obter_biometria_idnet_por_rg, obter_diretorio_download


APP_DIR = Path(__file__).parent
NIST_DIR = APP_DIR / "nists/rr/civil"
DOWNLOAD_DIR = NIST_DIR


def find_unique_files(directory=NIST_DIR):
    unique_files = set()
    
    # Walk através de todos os diretórios e subdiretórios
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Adiciona cada arquivo ao set, que automaticamente lida com duplicatas
            unique_files.add(file)
    
    # Retorna a lista de arquivos únicos
    return list(unique_files)


# Lê todo os arquivos do diretório recursivamente, excluindo os duplicados
ARQUIVOS_EXISTENTES = find_unique_files(NIST_DIR)


if __name__ == '__main__':
    
    lista_rgs = APP_DIR / 'lista_rgs_idnet.txt'

    with open(str(lista_rgs)) as f:
        rgs = f.read().splitlines()

        # print(f"{len(rgs)} RGs encontrados.")

    # # Em paralelo, baixa os dados e cria o nist
    # with ThreadPoolExecutor() as executor:
    #     # Submete cada arquivo para processamento paralelo
    #     result = executor.map(obter_biometria_idnet_por_rg, rgs)

    for rg in rgs:
        
        # Pula se o RG for maior que 300k, porque já têm biometria
        if int(rg) >= 300000:
            continue

        filename = f"rr-civil-rg{rg}.nst"
        rg_download_dir = obter_diretorio_download(rg)
        filepath = rg_download_dir / filename
        if filename in ARQUIVOS_EXISTENTES:
            print(f"[idnet] Arquivo já existe: {filepath}")
            continue

        try:
            nist_salvo = obter_biometria_idnet_por_rg(rg)
        except Exception as e:
            print(traceback.format_exc())


    print(f"Finalizado.")
