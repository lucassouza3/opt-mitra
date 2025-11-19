from zeep import Client, xsd
from zeep.transports import Transport
from requests import Session
import json
from datetime import datetime, timedelta
from base64 import b64decode, b64encode
from functions import formata_data_nascimento, formata_nome, validate_cpf, formata_sexo
import re
import traceback


def busca_wspolicia(operacao, body):

    if not isinstance(operacao, str):
        raise TypeError(f"Tipo {type(operacao)} inválida. Esperado <'str'>.")
    
    if not isinstance(body, dict):
        raise TypeError(f"Tipo {type(body)} inválido. Esperado <'dict'>.")

    wsdl = 'http://www.idnetbrasil.rr.gov.br/idNet.WebServicesnEW/Forms/wsPolicia.asmx?WSDL'

    client = Client(wsdl=wsdl)

    # Assuming the SOAP header needs to be set
    # Criar um header vazio
    header = xsd.Element(
        '{http://tempuri.org/}AuthHeader',
        xsd.ComplexType([])
    )
    header_value = header()

    # Make the call to the SOAP method
    # response = client.service[operacao](_soapheaders=[header_value], **body)
    response = client.service[operacao](**body)

    return response


def formata_rg(rg:int)-> int:
    str_rg = str(rg)
    if len(str_rg) > 6:
        novo_rg = str_rg[:-1]
        return int(novo_rg)
    else:
        return rg


def formata_result(result):
    if result:
        return json.loads(result.replace('result', '"result"'))


def requisicao_nominal(rg):
    if not isinstance(rg, str):
        raise TypeError(f"Tipo {type(rg)} inválida. Esperado <'str'>.")
    
    rg = formata_rg(rg)
    body = {'v_iRG': rg}

    print(f'Obtendo dados do cidadão do RG {rg}...')
    response = busca_wspolicia(operacao='RequisicaoNominal', body=body)
    if response:
        result = formata_result(response)["result"][0]
        if result:
            rg_atribuido = result["RGDVAtribuido"]
            if len(rg_atribuido) > 6:
                dvrg = rg_atribuido[-1]
            else:
                dvrg = ''

            nascimento = formata_data_nascimento(result["Nascimento"])

            pessoa = {
                "numero_pessoa": result["NumeroPessoa"],
                "nome": result["Nome"],
                "pai": result["FILIACAO_1"],
                "mae": result["FILIACAO_2"],
                "cpf": None,
                "nascimento": nascimento,
                "rg": rg_atribuido,
                "dvrg": dvrg
            }

            return pessoa


def obter_info_cidadao(numero_pessoa):
    
    body = {'v_sNumeroPessoa': numero_pessoa}
    infocidadao = busca_wspolicia("ObterInfoCidadao", body=body)
    if infocidadao:
        infocidadao = formata_result(infocidadao)        
        infocidadao = infocidadao["result"][0]

        rg = infocidadao["RGDVAtribuido"]

        try:
            # Remove caracteres não dígitos
            rg = re.sub(r'\D', '', rg)
            if len(rg) > 6:
                dvrg = rg[-1]
            else:
                dvrg = ''
        except:
            traceback.format_exc()
            print(json.dumps(infocidadao, indent=4))
            exit(-1)

        nascimento = datetime.fromisoformat(infocidadao["DataNascimentoAproximado"])    
        nascimento = formata_data_nascimento(nascimento)
        sexo = formata_sexo(infocidadao["DescricaoSexo"])

        pessoa = {
            "numero_pessoa": infocidadao["NumeroPessoa"],
            "nome": infocidadao["Nome"],
            "pai": infocidadao["Pai"],
            "mae": infocidadao["Mae"],
            "cpf": infocidadao["CPF"],
            "nascimento": nascimento,
            "cidade_nascimento": infocidadao["NomeMunicipioNascimento"],
            "sexo": sexo,
            "rg": rg,
            "dvrg": dvrg,
            "foto": infocidadao["FOTO"]
        }

        return pessoa


def idnet(nu_rg):
    result_pessoa = requisicao_nominal(nu_rg)

    if result_pessoa:
        nu_pessoa = result_pessoa["result"][0]["NumeroPessoa"]

        result_cidadao = requisicao_obter_info_cidadao(nu_pessoa)

        if result_cidadao:  # Se encontrou um cidadão para esse número de pessoa
            rg_atribuido = ''
            if result_cidadao["result"][0]["RGDVAtribuido"]:
                rg_atribuido = result_cidadao["result"][0]["RGDVAtribuido"]

            dt_nascimento = ''
            if result_cidadao["result"][0]["DataNascimentoAproximado"]:
                dt_nascimento = result_cidadao["result"][0]["DataNascimentoAproximado"].split('T')[0]
                try:
                    dt_nascimento = datetime.strptime(dt_nascimento, '%Y-%m-%d').strftime('%Y-%m-%d')
                except Exception as e:
                    logger.error(f'Erro na data de nascimento {dt_nascimento}')
                    dt_nascimento = ''

            nu_cpf = ''
            if result_cidadao["result"][0]["CPF"]:
                nu_cpf = result_cidadao["result"][0]["CPF"]
            no_mae = ''
            if result_cidadao["result"][0]["Mae"]:
                no_mae = result_cidadao["result"][0]["Mae"]

            no_pai = ''
            if result_cidadao["result"][0]["Pai"]:
                no_pai = result_cidadao["result"][0]["Pai"]

            if result_cidadao["result"][0]["FOTO"]:
                foto_arquivo = result_cidadao["result"][0]["FOTO"]

                pessoa = {
                    "nome": result_pessoa["result"][0]["Nome"],
                    "nascimento": dt_nascimento,
                    "mae": no_mae,
                    "pai": no_pai,
                    "cpf": nu_cpf,
                    "documento": rg_atribuido,
                    "sistema": "+IDNET",
                    "foto_arquivo": foto_arquivo
                    # "carga_inicial": True
                }

                dossier_ids = upload_findface(pessoa)
                if len(dossier_ids) > 0:
                    logger.info(f'Dossiê {dossier_ids} cadastrado com sucesso para o RG {nu_rg}.')
                    return 1
                else:
                    logger.info(f'Erro no cadastro do dossiê para o RG {nu_rg}')
                    return -2
            else:
                logger.info(f'RG {nu_rg} sem foto.')
                # Avança para o próximo rg sem salvar no arquivo de controle
                return -1
        else:
            logger.info(f'Nenhum cidadão encontrado para o "nu_pessoa" {nu_pessoa}')
            return 2
    else:
        logger.info(f'Nenhum registro encontardo para o RG {nu_rg}')
        return 0

    # with open(arquivos_enviados, 'a') as enviados:
    #     enviados.write(f'{nu_rg}\n')


if __name__ == '__main__':
    
    pessoa = requisicao_nominal(222921)

    print(pessoa["numero_pessoa"])

    body = {'v_sNumeroPessoa': pessoa["numero_pessoa"]}

    infocidadao = busca_wspolicia("ObterInfoCidadao", body=body)

    print(infocidadao)
