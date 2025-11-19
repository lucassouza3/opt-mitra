from detranrr.wsdetranrr import busca_por_cpf, busca_por_data, obter_arquivo_biometria
from NIST import NIST
from functions import *
from pathlib import Path
from datetime import datetime
from threader import Threader
from concurrent.futures import ThreadPoolExecutor
import traceback
import os
import shutil
import time



def find_unique_files(directory):
    unique_files = set()
    
    # Walk através de todos os diretórios e subdiretórios
    for root, dirs, files in os.walk(directory):
        for file in files:
            # Adiciona cada arquivo ao set, que automaticamente lida com duplicatas
            unique_files.add(file)
    
    # Retorna a lista de arquivos únicos
    return list(unique_files)


APP_DIR = Path(__file__).parent
DOWNLOAD_DIR = APP_DIR / "nists/rr/detran"

# Lê todo os arquivos do diretório recursivamente, excluindo os duplicados
ARQUIVOS_EXISTENTES = find_unique_files(DOWNLOAD_DIR)


def create_nist_detranrr(pessoa):

    # Extrai a data da coleta da pessoa
    data_coleta = datetime.strptime( pessoa["dt_coleta_biometria"], r"%Y-%m-%d %H:%M:%S" ).strftime(r"%Y-%m-%d")

    filename = f"rr-detran-cpf{pessoa['nu_cpf']}.nst"
    filepath = DOWNLOAD_DIR / f"{data_coleta}/{filename}"

    # Patch para corrigir os NISTs enviados por engano para o diretorio default 2024-01-01
    filepath_default =  DOWNLOAD_DIR / f'2024-01-01/{filename}'
    if filepath_default.exists():
        # Define the source and destination paths
        source = filepath_default
        destination = DOWNLOAD_DIR / data_coleta

        # Ensure the destination directory exists
        os.makedirs(os.path.dirname(destination), parents=True, exist_ok=True)

        # Move the file
        shutil.move(source, destination)
        print(f"[patch] Arquivo movido para o destino {filepath_detino}")
        return

    # Cria o diretório se não existe
    filepath.parent.mkdir(parents=True, exist_ok=True)

    print(f"[baixa_detranrr] Baixando dados do CPF {pessoa['nu_cpf']} em {filepath}")

    dedos = [ 
        'dedo_polegar_direito',
        'dedo_indicador_direito',
        'dedo_medio_direito',
        'dedo_anelar_direito',
        'dedo_minimo_direito',
        'dedo_polegar_esquerdo',
        'dedo_indicador_esquerdo',
        'dedo_medio_esquerdo',
        'dedo_anelar_esquerdo',
        'dedo_minimo_esquerdo'            
    ]

    try:
        # Cria o NIST
        new_nist = NIST()
        new_nist.add_Type01()
        new_nist.add_Type02()

        # Base de Origem
        new_nist.set_field('1.008', 'RR/DETRAN', idc=0)  # Base de Origem
        
        new_nist.set_field('2.030', formata_nome(pessoa["no_nome"]), idc=0)  # Nome
        new_nist.set_field('2.035', formata_data_nascimento(pessoa["dt_nascimento"]), idc=0)  # Data de nascimento
        new_nist.set_field('2.037', None, idc=0)  # Cidade de nascimento
        new_nist.set_field('2.038', None, idc=0)  # País de nascimento
        new_nist.set_field('2.039', None, idc=0)  # Sexo 1|M-Masculino, 2|F-Feminino, ?|O-Outros
        new_nist.set_field('2.201', formata_nome(pessoa["no_pai"]), idc=0)  # Pai
        new_nist.set_field('2.202', formata_nome(pessoa["no_mae"]), idc=0)  # Mae
        new_nist.set_field('2.211', None)  # Identidade
        new_nist.set_field('2.212', validate_cpf(pessoa["nu_cpf"]), idc=0),  # CPF
        # new_nist.set_field('2.213', '', idc=0)  # Titulo de eleitor
        # new_nist.set_field('2.214', '', idc=0)  # CNH
        new_nist.set_field('2.224', None, idc=0)  # Nome social

        # # Faces
        new_nist.add_ntype(10)
        new_nist.add_idc(10, 1)
        face = obter_arquivo_biometria(pessoa["biometria"]["face"])
        new_nist.set_field('10.999', face, idc=1)

        # Assinatura
        # new_nist.add_ntype(8)
        # new_nist.add_idc(8, 1)
        # assinatura = formata_imagem(obter_arquivo_biometria(pessoa["biometria"]["assinatura"]))
        # new_nist.set_field('8.999', assinatura)

        # Digitais
        new_nist.add_ntype(4)        
        for idc in range(1, 11):
            new_nist.add_idc(4, idc)
            digital = obter_arquivo_biometria(pessoa["biometria"][dedos[idc-1]])
            new_nist.add_ntype(4)
            new_nist.set_field('4.001', 4, idc=idc)  # Record Type (TYP) [Mandatory]
            new_nist.set_field('4.002', idc, idc=idc)  # Image Designation Character (IDC) [Mandatory]
            new_nist.set_field('4.003', 1, idc=idc)  # Impression Type (IMP) [Mandatory]
            new_nist.set_field('4.004', idc, idc=idc)  # Finger Position (FGP) [Mandatory]
            new_nist.set_field('4.005', 1, idc=idc)  # Fingerprint Image Scanning Resolution (FIR) [Mandatory] 
            new_nist.set_field('4.006', 800, idc=idc)  # Image Horizontal Line Length (HLL) [Mandatory]
            new_nist.set_field('4.007', 750, idc=idc)  # Image Vertical Line Length (VLL) [Mandatory]
            new_nist.set_field('4.008', 1, idc=idc)  # Image Compression Algorithm (ICA) [Mandatory]
            new_nist.set_field('4.999', digital, idc=idc)  # Image binary
    
    except Exception as e:
        print(traceback.format_exc())
        return None
    
    # Patch para evitar bug desconhecido na gravação do NIST no disco
    try:
        new_nist.write(filepath)
    except:
        traceback.format_exc()
        return

    return new_nist


def busca_por_cpf_paralelo(cpf):
    filename = f"rr-detran-cpf{cpf}.nst"
    if filename in ARQUIVOS_EXISTENTES:
        print(f"[baixa_detranrr] Arquivo já existe: {filename}")
        return

    pessoa = busca_por_cpf(cpf)
    print(f'Buscando CPF {cpf}...')
    if pessoa:
        return create_nist_detranrr(pessoa)
    else:
        print(f'Nenhuma pessoa encontrada para o CPF "{cpf}".')


if __name__ == '__main__':

    root_dir = Path(__file__).parent
    arquivo_cpfs = root_dir / 'detranrr-cpfs-ate-06-04-2024.txt'

    with open(str(arquivo_cpfs)) as f:
        lista_cpfs = f.read().splitlines()

        print(f"{len(lista_cpfs)} CPFs encontrados.")

    # Em paralelo, baixa os dados e cria o nist
    # with ThreadPoolExecutor() as executor:
    #     result = executor.map(busca_por_cpf_paralelo, lista_cpfs)

    # Pesquisa sequencial
    for cpf in lista_cpfs:
        pessoa = busca_por_cpf_paralelo(cpf)

    print(f"Finalizado.")

