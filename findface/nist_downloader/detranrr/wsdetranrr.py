import requests
import urllib3
from pathlib import Path
from functions import *


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


BASE_URL = "https://uci-dados-api.searchtecnologia.com.br"


def obter_certificados():
    base_dir = Path(__file__).parent
    certificado_digital = base_dir / 'certificado-pf-rr.crt'
    chave_privada = base_dir / 'chave-privada.key'
    if not certificado_digital.exists():
        raise Exception(f'Certificado digital não encontrado.')
    if not chave_privada.exists():
        raise Exception(f'Chave privada não encontrad.')

    return certificado_digital, chave_privada


def busca_por_cpf(cpf: str) -> dict:

    certificado_digital, chave_privada = obter_certificados()

    cpf = validate_cpf(cpf)
    if not cpf:
        raise Exception("CPF inválido.")

    cpf_info_url = f"{BASE_URL}/biometria/cpf/{cpf}"
    response = requests.get(cpf_info_url, cert=(str(certificado_digital), str(chave_privada)), verify=False)

    if 200 <= response.status_code < 300:
        if response.json()['dados'][0] is None:
            return None

        return response.json()['dados'][0]


def busca_por_data(data_pesquisa: str) -> list:
    certificado_digital, chave_privada = obter_certificados()    

    data_pesquisa = formata_data_nascimento(data_pesquisa)
    
    biometria_download_base_url = f"{BASE_URL}/biometria/data/{data_pesquisa}"
    response = requests.get(biometria_download_base_url, cert=(str(certificado_digital), str(chave_privada)), verify=False)

    if 200 <= response.status_code < 300:
        if 'dados' not in response.json():
            return []

        return response.json()['dados']


def obter_arquivo_biometria(id_biometria: str) -> bytes:
    certificado_digital, chave_privada = obter_certificados()
    
    biometria_download_base_url = f"{BASE_URL}/biometria/arquivo/{id_biometria}"
    response = requests.get(biometria_download_base_url, cert=(str(certificado_digital), str(chave_privada)), verify=False)

    if 200 <= response.status_code < 300:
        return response.content
    else:
        return None
