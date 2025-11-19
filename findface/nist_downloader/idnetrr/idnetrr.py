from . import wsPolicia, wscivil
from pathlib import Path
from datetime import datetime, timedelta
from NIST import NIST
from functions import *
import traceback
import os
import base64
import json


APP_DIR = Path(__file__).parent.parent
NIST_DIR = APP_DIR / "nists/rr/civil"
DOWNLOAD_DIR = NIST_DIR


def obter_diretorio_download(rg):
    subdiretorio = hash_to_3_digits(int(rg))
    rg_download_dir = DOWNLOAD_DIR / str(subdiretorio)

    return rg_download_dir


def hash_to_3_digits(number):
    # Obtem o módulo 1000 do número para garantir que estará entre 0 e 999
    hashed_number = number % 1000
    
    # Formata o número para garantir que tenha 3 dígitos
    formatted_number = f"{hashed_number:03}"
    
    return formatted_number


def obter_biometria_idnet_por_rg(rg):
    cidadao = wsPolicia.requisicao_nominal(rg)

    if cidadao:

        info_cidadao = wsPolicia.obter_info_cidadao(cidadao["numero_pessoa"])

        # Debug
        # print(json.dumps(cidadao, indent=4))
        # exit(-1)

        if info_cidadao:
            print(f"Buscando biometria do RG {rg}...")

            documento = str(info_cidadao['rg'])

            # Cria o NIST
            new_nist = NIST()
            new_nist.add_Type01()
            new_nist.add_Type02()

            # Base de Origem
            new_nist.set_field('1.008', 'RR/CIVIL', idc=0)  # Base de Origem
            
            new_nist.set_field('2.030', formata_nome(info_cidadao['nome']), idc=0)  # Nome
            new_nist.set_field('2.035', formata_data_nascimento(info_cidadao['nascimento']), idc=0)  # Data de nascimento
            new_nist.set_field('2.037', formata_nome(info_cidadao["cidade_nascimento"]), idc=0)  # Cidade de nascimento
            new_nist.set_field('2.038', None, idc=0)  # País de nascimento
            new_nist.set_field('2.039', formata_sexo(info_cidadao["sexo"]), idc=0)  # Sexo 1|M-Masculino, 2|F-Feminino, ?|O-Outros
            new_nist.set_field('2.201', formata_nome(info_cidadao['pai']), idc=0)  # Pai
            new_nist.set_field('2.202', formata_nome(info_cidadao['mae']), idc=0)  # Mae
            new_nist.set_field('2.211', formata_documento(documento))  # Documento de Identidade (RG)
            new_nist.set_field('2.212', validate_cpf(info_cidadao['cpf']), idc=0),  # CPF
            # new_nist.set_field('2.213', '', idc=0)  # Titulo de eleitor
            # new_nist.set_field('2.214', '', idc=0)  # CNH
            new_nist.set_field('2.224', None, idc=0)  # Nome social

            # Assinatura
            # new_nist.add_ntype(8)
            # new_nist.add_idc(8, 1)
            # assinatura = convert_to_jpeg(wscivil.obter_assinatura(info_cidadao['numero_pessoa']))
            # new_nist.set_field('8.999', assinatura, idc=1)

            # face = convert_to_jpeg(wscivil.obter_foto_3x4(info_cidadao['numero_pessoa']))
            if info_cidadao["foto"] is not None and isinstance(info_cidadao["foto"], str):
                # Faces
                new_nist.add_ntype(10)
                new_nist.add_idc(10, 1)
                face = base64.b64decode(info_cidadao["foto"])
                new_nist.set_field('10.999', face, idc=1)

                filename = f"rr-civil-rg{rg}.nst"
                rg_download_dir = obter_diretorio_download(rg)
                filepath = rg_download_dir / f"rr-civil-rg{documento}.nst"

                new_nist.write(filepath)
                print(f'[idnet] NIST salvo com sucesso. {filepath}')

                return new_nist
            
            else:
                print(f"RG {rg} sem foto.")


if __name__ == '__main__':
    obter_biometria_idnet_por_rg(222921)