from detranrr.wsdetranrr import busca_por_cpf, busca_por_data, obter_arquivo_biometria
from detranrr_baixar import create_nist_detranrr
from NIST import NIST
from functions import *
from pathlib import Path
from datetime import datetime, timedelta
import json
from threader import Threader
from concurrent.futures import ThreadPoolExecutor
    

if __name__ == '__main__':

    root_dir = Path(__file__).parent
    arquivo_dt_ultima_atualizacao = root_dir / 'data_ultima_atualizacao_detranrr.txt'

    if not arquivo_dt_ultima_atualizacao.exists():
        raise FileNotFoundError(f"Arquivo '{arquivo_dt_ultima_atualizacao}' não encontrado.")

    with arquivo_dt_ultima_atualizacao.open('r') as f:
        data_ultima_atualizacao = f.read().splitlines()[0]

    data_ultima_atualizacao = datetime.strptime(data_ultima_atualizacao, r'%Y-%m-%d')

    while data_ultima_atualizacao.date() < datetime.now().date():

        print(f"Lendo {data_ultima_atualizacao.strftime(r'%Y-%m-%d')}...")

        lista_pessoas = busca_por_data(data_ultima_atualizacao.strftime(r'%Y-%m-%d'))
        if lista_pessoas is None:
            print(f"Data pesquisada '{data_ultima_atualizacao.strftime(r'%Y-%m-%d')}' é anterior ao permitido.")
        else:
            if lista_pessoas:
                print(f"{len(lista_pessoas)} pessoas encontradas.")
                # Em paralelo, cria os nists
                # with ThreadPoolExecutor() as executor:
                #     result = executor.map(create_nist_detranrr, lista_pessoas)

                # Em sequência
                for pessoa in lista_pessoas:
                    try:
                        create_nist_detranrr(pessoa)
                    except Exception as e:
                        print(str(e))
            else:
                print(f"Nenhuma coleta biometrica encontrada na data {data_ultima_atualizacao.strftime(r'%Y-%m-%d')}")

        # Atualiza o arquivo com a data da última atualização lida
        with arquivo_dt_ultima_atualizacao.open('w') as f:
            f.write(data_ultima_atualizacao.strftime(r'%Y-%m-%d'))

        data_ultima_atualizacao = data_ultima_atualizacao + timedelta(days=1)
    
    print(f"Finalizado.")