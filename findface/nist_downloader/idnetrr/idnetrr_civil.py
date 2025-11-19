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

    info_cidadao = wscivil.busca_cidadao_por_rg(rg)

    if info_cidadao:
        print(f"Buscando biometria do RG {rg}...")

        # Obtem o Dígito Verificador (DV) do RG
        dvrg = "" if str(info_cidadao["dvrg"]) is None else str(info_cidadao["dvrg"])

        # Acrescenta o DV ao RG
        documento = str(info_cidadao["rg"]) + dvrg

        # Cria o NIST
        new_nist = NIST()
        new_nist.add_Type01()
        new_nist.add_Type02()

        # Base de Origem
        new_nist.set_field('1.008', 'RR/CIVIL', idc=0)  # Base de Origem
        
        new_nist.set_field('2.030', formata_nome(info_cidadao['nome']), idc=0)  # Nome
        new_nist.set_field('2.035', formata_data_nascimento(info_cidadao['nascimento']), idc=0)  # Data de nascimento
        # new_nist.set_field('2.037', formata_nome(info_cidadao["cidade_nascimento"]), idc=0)  # Cidade de nascimento
        # new_nist.set_field('2.038', None, idc=0)  # País de nascimento
        # new_nist.set_field('2.039', formata_sexo(info_cidadao["sexo"]), idc=0)  # Sexo 1|M-Masculino, 2|F-Feminino, ?|O-Outros
        new_nist.set_field('2.201', formata_nome(info_cidadao['pai']), idc=0)  # Pai
        new_nist.set_field('2.202', formata_nome(info_cidadao['mae']), idc=0)  # Mae
        new_nist.set_field('2.211', formata_documento(documento))  # Documento de Identidade (RG)
        new_nist.set_field('2.212', validate_cpf(info_cidadao['cpf']), idc=0),  # CPF
        # new_nist.set_field('2.213', '', idc=0)  # Titulo de eleitor
        # new_nist.set_field('2.214', '', idc=0)  # CNH
        # new_nist.set_field('2.224', None, idc=0)  # Nome social

        # Assinatura
        # new_nist.add_ntype(8)
        # new_nist.add_idc(8, 1)
        # assinatura = convert_to_jpeg(wscivil.obter_assinatura(info_cidadao['numero_pessoa']))
        # new_nist.set_field('8.999', assinatura, idc=1)

        foto3x4 = wscivil.obter_foto_3x4(info_cidadao['numero_pessoa'])
        if foto3x4:
            face = convert_to_jpeg(foto3x4)
            if face:
                # Faces
                new_nist.add_ntype(10)
                new_nist.add_idc(10, 1)
                new_nist.set_field('10.999', face, idc=1)
            else:
                print(f"RG {rg} sem foto.")
                return

            # Digitais
            for dedo in range(1, 11):
                digital = wscivil.obter_digital(info_cidadao['numero_pessoa'], dedo)

                new_nist.add_ntype(4)
                new_nist.set_field('4.001', 4, idc=dedo)  # Record Type (TYP) [Mandatory]
                new_nist.set_field('4.002', dedo, idc=dedo)  # Image Designation Character (IDC) [Mandatory]
                new_nist.set_field('4.003', 1, idc=dedo)  # Impression Type (IMP) [Mandatory]
                new_nist.set_field('4.004', dedo, idc=dedo)  # Finger Position (FGP) [Mandatory]
                new_nist.set_field('4.005', 1, idc=dedo)  # Fingerprint Image Scanning Resolution (FIR) [Mandatory]
                new_nist.set_field('4.006', 800, idc=dedo)  # Image Horizontal Line Length (HLL) [Mandatory]
                new_nist.set_field('4.007', 700, idc=dedo)  # Image Vertical Line Length (VLL) [Mandatory]
                new_nist.set_field('4.008', 1, idc=dedo)  # Print Position Coordinates (PPC) [Optional]
                new_nist.set_field('4.014', 'WSQ', idc=dedo)  # Image Compression Algorithm (ICA) [Mandatory]
                new_nist.set_field('4.999', digital, idc=dedo)

            filename = f"rr-civil-rg{rg}.nst"
            rg_download_dir = obter_diretorio_download(rg)
            filepath = rg_download_dir / f"rr-civil-rg{documento}.nst"

            new_nist.write(filepath)
            print(f'[idnetrr_civil] NIST salvo com sucesso. {filepath}')

            # print(new_nist.dump())

            return new_nist
        else:
            print(f"Nenhuma foto encontrada para o RG {rg}")


if __name__ == '__main__':
    obter_biometria_idnet_por_rg(222921)