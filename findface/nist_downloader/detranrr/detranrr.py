import requests
import urllib3
from ..biometria import Biometria
from pathlib import Path


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_biometric_data_from_detranrr(cpf: str) -> Biometria:
    base_dir = Path(__file__).parent
    certificado_digital = base_dir / 'certificado-pf-rr.crt'
    chave_privada = base_dir / 'chave-privada.key'
    if not certificado_digital.exists():
        raise Exception(f'Certificado digital não encontrado.')
    if not chave_privada.exists():
        raise Exception(f'Chave privada não encontrad.')

    base_url = "https://uci-dados-api.searchtecnologia.com.br"
    cpf_info_url = f"{base_url}/biometria/cpf/{cpf}"
    biometria_download_base_url = f"{base_url}/biometria/arquivo/"
    response = requests.get(cpf_info_url, cert=(str(certificado_digital), str(chave_privada)), verify=False)

    if 200 <= response.status_code < 300:
        if response.json()['dados'][0] is None:
            return None

        data = response.json()['dados'][0]
        
        # Instancia a biometria com os dados ONOMÁSTICOS
        bio = Biometria(nome=data['no_nome'], nascimento=data['dt_nascimento'], mae=data['no_mae'], pai=data['no_pai'],
                        nacionalidade=data['pais_nascimento'], cpf=data['nu_cpf'], documento=None, data_coleta=data['dt_coleta_biometria'],
                        passaporte=None, rnm=None, face=None, assinatura=None, dedo_polegar_direito=None, dedo_indicador_direito=None, 
                        dedo_medio_direito=None, dedo_anelar_direito=None, dedo_minimo_direito=None, dedo_polegar_esquerdo=None, dedo_indicador_esquerdo=None, 
                        dedo_medio_esquerdo=None, dedo_anelar_esquerdo=None, dedo_minimo_esquerdo=None) 
        
        # Carrega os dados BIOMÉTRICOS
        biometrics = data['biometria']
        images = {}

        # Fetch and verify each biometric image
        for key, bio_id in biometrics.items():
            bio_file_url = f"{biometria_download_base_url}{bio_id}"
            bio_response = requests.get(bio_file_url, cert=(str(certificado_digital), str(chave_privada)), verify=False)
            if 200 <= bio_response.status_code < 300:
                images[key] = bio_response.content
                if key == 'face':
                    bio.face = bio_response.content
                if key == 'assinatura':
                    bio.assinatura = bio_response.content
                if key == 'dedo_polegar_direito':
                    bio.dedo_polegar_direito = bio_response.content
                if key == 'dedo_indicador_direito':
                    bio.dedo_indicador_direito = bio_response.content
                if key == 'dedo_medio_direito':
                    bio.dedo_medio_direito = bio_response.content
                if key == 'dedo_anelar_direito':
                    bio.dedo_anelar_direito = bio_response.content
                if key == 'dedo_minimo_direito':
                    bio.dedo_minimo_direito = bio_response.content                
                if key == 'dedo_polegar_esquerdo':
                    bio.dedo_polegar_esquerdo = bio_response.content
                if key == 'dedo_indicador_esquerdo':
                    bio.dedo_indicador_esquerdo = bio_response.content
                if key == 'dedo_medio_esquerdo':
                    bio.dedo_medio_esquerdo = bio_response.content
                if key == 'dedo_anelar_esquerdo':
                    bio.dedo_anelar_esquerdo = bio_response.content
                if key == 'dedo_minimo_esquerdo':
                    bio.dedo_minimo_esquerdo = bio_response.content

                print(f"{key} lido(a) com sucesso!")
    
        return bio

if __name__ == '__main__':
    pass        