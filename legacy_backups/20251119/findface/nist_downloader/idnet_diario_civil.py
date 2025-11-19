from NIST import NIST
from functions import *
from pathlib import Path
from datetime import datetime, timedelta
import json
from threader import Threader
from idnetrr.idnetrr_civil import obter_biometria_idnet_por_rg, obter_diretorio_download
import traceback


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


if __name__ == '__main__':
    # Busca novos RGs
    rgs = obter_lista_rgs_processados()
    ultimo_rg = int(rgs[-1])
    print('Ultimo RG lido:', ultimo_rg)
    falhas = 0
    proximo_rg = ultimo_rg

    while True:
        proximo_rg += 1
        try:
            nist = obter_biometria_idnet_por_rg(str(proximo_rg))

            if not nist:
                falhas += 1
                print(f"[idnet_atualizar] Falha na obtenção do RG {proximo_rg}. Tetativa {falhas}...")
            else:
                lista_rgs = APP_DIR / "lista_rgs_idnet.txt"
                with open(lista_rgs, 'a') as f:
                    f.write(f'{str(proximo_rg)}\n')
        except Exception as e:
            print(traceback.format_exc())

        if falhas == 5:
            break
