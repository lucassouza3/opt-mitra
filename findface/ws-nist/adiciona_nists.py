from app import app
from database.models import db, Nist, BaseOrigem, BaseOrigemFindface, Findface, NistFindface, Log
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from nist_manager import add_nist_to_db_by_uri, add_log
import hashlib
import traceback
from datetime import datetime, timedelta


def listar_arquivos_nst(diretorio):
    """
    Gera o caminho completo de todos os arquivos com extensão '.nst' dentro de um diretório especificado.

    Args:
    diretorio (str): O caminho do diretório onde os arquivos serão listados.

    Yields:
    str: O caminho completo de cada arquivo '.nst' encontrado.
    """
    arquivos = []
    diretorio_path = Path(diretorio).resolve()
    for dirpath, dirnames, filenames in os.walk(diretorio_path):
        for filename in filenames:
            if filename.endswith('.nst'):
                yield os.path.join(dirpath, filename)
                # arquivos.append(os.path.join(dirpath, filename))

    # return arquivos


def listar_diretorios_com_nst(root_dir):
    """
    Gera o caminho completo de todos os diretórios em 'root_dir' que contêm ao menos um arquivo com a extensão '.nst',
    recursivamente. Segue links simbólicos.

    Args:
    root_dir (str): O caminho do diretório raiz.

    Yields:
    str: Caminho completo dos diretórios que contêm arquivos '.nst'.
    """
    # Certifique-se de que o caminho está absoluto e resolvido (segue links simbólicos)
    root_dir = Path(root_dir).resolve()

    lista_diretorios_com_nist = []

    for dirpath, dirnames, filenames in os.walk(root_dir, followlinks=True):
        # Verifica se há algum arquivo com a extensão '.nst' no diretório atual
        if any(filename.endswith('.nst') for filename in filenames):
            yield dirpath
            # lista_diretorios_com_nist.append(dirpath)

    # return lista_diretorios_com_nist


def processa_arquivo_nist_em_paralelo(nist_filepath):
    with app.app_context() as context:
        novo_nist = add_nist_to_db_by_uri(nist_filepath)    
        return novo_nist

    
def processa_diretorio_em_paralelo(diretorio):
    """
    Lista todos os arquivos '.nst' de um diretório e executa uma função de processamento em paralelo em cada arquivo.

    Args:
    diretorio (str): O caminho do diretório de onde os arquivos NIST serão processados.
    """
    with ThreadPoolExecutor() as executor:
        # Cria um gerador para os arquivos '.nst'
        arquivos_nst = listar_arquivos_nst(diretorio)
        # Submete cada arquivo para processamento paralelo
        result = executor.map(processa_arquivo_nist_em_paralelo, arquivos_nst)


if __name__ == '__main__':

    # Diretório root onde os arquivos .nst estão localizados
    root_dir = Path(__file__).parent / 'nists'

    timestamp_inicial = datetime.now()
    # print(timestamp_inicial.strftime(r'%Y-%m-%d %H:%M:%S'), "- início")

    # Processamento manual
    for diretorio in listar_diretorios_com_nst(root_dir):
        print(f"Processando diretório {diretorio}...")
        processa_diretorio_em_paralelo(diretorio)

    timestamp_final = datetime.now()
    # print(timestamp_final.strftime(r'%Y-%m-%d %H:%M:%S'), "- fim")
    tempo_transcorrido = timestamp_final - timestamp_inicial
    dias = tempo_transcorrido.days
    # Obtendo as horas, minutos e segundos a partir dos segundos totais restantes
    total_segundos_restantes = tempo_transcorrido.seconds
    horas = total_segundos_restantes // 3600
    minutos = (total_segundos_restantes % 3600) // 60
    segundos = total_segundos_restantes % 60
    print(f"Tempo transcorrido: {dias} dias, {horas}:{minutos}:{segundos}")    
    print(f"Concluído.")    