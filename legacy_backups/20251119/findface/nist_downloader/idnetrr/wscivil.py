from zeep import Client, xsd
from zeep.transports import Transport
from requests import Session
import json
from datetime import datetime, timedelta
from base64 import b64decode, b64encode


def busca_wscivil(operacao, body):

    if not isinstance(operacao, str):
        raise TypeError("Tipo <operacao> inválida. Esperado 'str'.")
    
    if not isinstance(body, dict):
        raise TypeError("Tipo <body> inválido. Esperado 'dict'.")

    wsdl = 'http://www.idnetbrasil.rr.gov.br/idNet.WebServices/Forms/wscivil.asmx?WSDL'
    client = Client(wsdl)

    # Assuming the SOAP header needs to be set
    header = xsd.Element(
        '{http://tempuri.org/}AuthHeader',
        xsd.ComplexType([
            xsd.Element('{http://tempuri.org/}Usuario', xsd.String()),
            xsd.Element('{http://tempuri.org/}Senha', xsd.String()),
            xsd.Element('{http://tempuri.org/}Key', xsd.String()),
        ])
    )
    header_value = header(Usuario='PFRR', Senha='PFRR2024', Key='1')
    # Make the call to the SOAP method
    # response = client.service.BuscarPorRG(_soapheaders=[header_value], v_iRG='222921')
    response = client.service[operacao](_soapheaders=[header_value], **body)

    return response


def formata_rg(rg:int)-> int:
    str_rg = str(rg)
    if len(str_rg) > 6:
        novo_rg = str_rg[:-1]
        return int(novo_rg)
    else:
        return rg


def busca_cidadao_por_rg(rg):
   
    rg = formata_rg(rg)
    body = {'v_iRG': rg}

    print(f'Obtendo dados do cidadão do RG {rg}...')
    response = busca_wscivil(operacao='BuscarPorRG', body=body)

    if response:
        try:
            cidadao = response['_value_1'][1]['_value_1'][0]['Table']
        except:
            return None

        pessoa = {
            "numero_pessoa": cidadao.NUMEROPESSOA,
            "nome": cidadao.NOME,
            "pai": cidadao.PAI,
            "mae": cidadao.MAE,
            "cpf": cidadao.CPF,
            "nascimento": cidadao.NASCIMENTOAPROXIMADO.strftime(r'%Y-%m-%d'),
            "rg": cidadao.RGATRIBUIDO,
            "dvrg": cidadao.DVRGATRIBUIDO
        }

        return pessoa


def obter_foto_3x4(numero_pessoa):

    if not isinstance(numero_pessoa, int):
        raise TypeError(f"<numero_pessoa> inválido. Esperado inteiro 'int', informado {type(numero_pessoa)}")
    
    body = {
        'v_iPessoa': numero_pessoa
    }
    print('Obtendo foto 3x4...')
    response = busca_wscivil(operacao='ObterFoto3x4', body=body)

    if response:
        return response
    

def obter_digital(numero_pessoa, numero_dedo):
    
    if not isinstance(numero_pessoa, int):
        raise TypeError(f"<numero_pessoa> inválido. Esperado inteiro 'int', informado {type(numero_pessoa)}")
    
    if not isinstance(numero_dedo, int):
        raise TypeError(f"<numero_dedo> inválido. Esperado inteiro 'int', informado {type(numero_dedo)}")

    body = {
        'v_iPessoa': numero_pessoa,
        'v_iPosicao': numero_dedo
    }

    print(f'Obtendo digital #{numero_dedo}...')
    response = busca_wscivil(operacao='ObterDigitais', body=body)

    if response:
        return response


def obter_assinatura(numero_pessoa):

    if not isinstance(numero_pessoa, int):
        raise TypeError(f"<numero_pessoa> inválido. Esperado inteiro 'int', informado {type(numero_pessoa)}")
    
    body = {
        'v_iPessoa': numero_pessoa
    }
    print('Obtendo assinatura...')
    response = busca_wscivil(operacao='ObterAssinatura', body=body)

    if response:
        return response


if __name__ == '__main__':
    
    cidadao = busca_cidadao_por_rg(222921)
    assinatura = obter_assinatura(cidadao['numero_pessoa'])

    # with open('assinatura.jpg', 'wb') as file:
    #     file.write(assinatura)
