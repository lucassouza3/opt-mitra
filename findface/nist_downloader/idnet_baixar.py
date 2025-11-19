from NIST import NIST
from functions import *
from pathlib import Path
from datetime import datetime, timedelta
import json
from idnetrr.idnetrr_civil import obter_biometria_idnet_por_rg, obter_diretorio_download
import traceback
from concurrent.futures import ThreadPoolExecutor
import os


APP_DIR = Path(__file__).parent
NIST_DIR = APP_DIR / "nists/rr/civil"
data_hoje = datetime.now().strftime(r'%Y-%m-%d')
DOWNLOAD_DIR = NIST_DIR 


def read_last_line(filename):
    with open(filename, 'rb') as file:
        file.seek(-2, 2)  # Move o ponteiro para o segundo byte antes do fim do arquivo
        while file.read(1) != b'\n':  # Retrocede até encontrar o próximo caractere de nova linha
            file.seek(-2, 1)
        last_line = file.readline().decode()  # Lê a última linha e decodifica para string
    
    return last_line


def obter_ultimo_rg_processado():
    lista_rgs = APP_DIR / 'lista_rgs_idnet.txt'

    return read_last_line(lista_rgs)


def obter_lista_rgs_processados():
    lista_rgs = APP_DIR / 'lista_rgs_idnet.txt'

    with open(str(lista_rgs)) as f:
        rgs = f.read().splitlines()

    return rgs


def process_rg(rg):
    return obter_biometria_idnet_por_rg(str(rg))


if __name__ == '__main__':
    num_cpus = os.cpu_count()  # Obtém o número de CPUs disponíveis no sistema

    with ThreadPoolExecutor(max_workers=num_cpus) as executor:
        try:
            # Use executor.map para aplicar process_rg a cada RG na faixa especificada
            results = list(executor.map(process_rg, range(600000, 800000)))
        except:
            print(traceback.format_exc())            

    # Opcionalmente, você pode processar os resultados aqui
    # for rg, nist in zip(range(1, 700000), results):
        # Faça algo com os resultados, se necessário
        # pass

