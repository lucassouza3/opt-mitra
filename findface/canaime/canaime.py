import os
import requests
import yaml
from typing import Dict, Any
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from NIST import NIST
from NIST3.functions_mitra_toolkit import formata_data_nascimento, formata_documento, formata_nome, formata_sexo
import mylogger

# Logger
logger = mylogger.configurar_logger('canaime.log')


def ler_configuracao_yaml(caminho_arquivo: str) -> Dict[str, Any]:
    if not isinstance(caminho_arquivo, str):
        raise TypeError("caminho_arquivo deve ser uma string")

    with open(caminho_arquivo, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
            if config is None:
                config = {}
            return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Erro ao processar o arquivo YAML: {e}")


def base_para_nome_arquivo(base_nome: str) -> str:
    if not isinstance(base_nome, str):
        raise TypeError("base_nome deve ser uma string")
    return base_nome.replace('/', '.')


def ler_ultimo_id(base_nome: str) -> int:
    nome_arquivo = base_para_nome_arquivo(base_nome) + '.txt'
    if not os.path.exists(nome_arquivo):
        return 0

    with open(nome_arquivo, 'r') as f:
        try:
            return int(f.read().strip())
        except ValueError:
            return 0


def salvar_ultimo_id(base_nome: str, ultimo_id: int) -> None:
    nome_arquivo = base_para_nome_arquivo(base_nome) + '.txt'
    with open(nome_arquivo, 'w') as f:
        f.write(str(ultimo_id))


def fazer_requisicao(token: str, usuario: str, senha: str, pagina: int, id: int) -> Dict[str, Any]:
    url = 'http://canaime.com.br/mitrarr/index.php'
    data = {'token': token, 'usuario': usuario, 'senha': senha, 'pagina': pagina, 'id': id}

    response = requests.post(url, data=data)
    response.raise_for_status()
    return response.json()


def download_imagem(url_foto: str) -> bytes:
    response = requests.get(url_foto)
    response.raise_for_status()
    return response.content


def gera_nist_canaime(dados_pessoa: dict, foto: bytes, base_nome: str, caminho_destino: str) -> None:
    new_nist = NIST()
    new_nist.add_Type01()
    new_nist.add_Type02()

    nome = formata_nome(dados_pessoa.get('nome'))
    nascimento = formata_data_nascimento(dados_pessoa.get('dn'), r'%Y%m%d')
    mae = formata_nome(dados_pessoa.get('mae'))
    pai = formata_nome(dados_pessoa.get('pai'))
    cidade_nascimento = formata_nome(dados_pessoa.get('cidade_nasc'))
    pais_nascimento = formata_nome(dados_pessoa.get('pais_nasc'))
    cpf = formata_documento(dados_pessoa.get('cpf'))
    documento = formata_documento(dados_pessoa.get('rg'))
    sexo = formata_sexo(dados_pessoa.get('sexo'))

    new_nist.set_field('1.008', base_nome, idc=0)
    new_nist.set_field('2.030', nome, idc=0)
    new_nist.set_field('2.035', nascimento, idc=0)
    new_nist.set_field('2.037', cidade_nascimento, idc=0)
    new_nist.set_field('2.038', pais_nascimento, idc=0)
    new_nist.set_field('2.039', sexo, idc=0)
    new_nist.set_field('2.201', pai, idc=0)
    new_nist.set_field('2.202', mae, idc=0)
    new_nist.set_field('2.211', documento)
    new_nist.set_field('2.212', cpf, idc=0)

    new_nist.add_ntype(10)
    new_nist.set_field('10.999', foto, idc=1)
    new_nist.write(caminho_destino)


def processar_pagina(token: str, usuario: str, senha: str, base_nome: str, pagina: int) -> None:
    logger.info(f"[Base: {base_nome} | Página: {pagina}] Iniciando processamento...")

    ultimo_id_lido = ler_ultimo_id(base_nome)
    id_atual = ultimo_id_lido + 1

    try:
        resposta = fazer_requisicao(token, usuario, senha, pagina, id_atual)
    except Exception as e:
        logger.error(f"[Base: {base_nome} | Página: {pagina}] Erro na requisição inicial: {e}")
        return

    if not resposta or 'ultimo_id' not in resposta:
        logger.info(f"[Base: {base_nome} | Página: {pagina}] Nenhum dado encontrado.")
        return

    ultimo_id = int(resposta.get('ultimo_id', id_atual))

    while id_atual <= ultimo_id:
        try:
            resposta = fazer_requisicao(token, usuario, senha, pagina, id_atual)

            if not resposta or not resposta.get('id'):
                logger.info(f"[Base: {base_nome} | Página: {pagina}] ID {id_atual} não retornou dados válidos, ignorando.")
                id_atual += 1
                continue

            url_foto = resposta.get('url_foto')
            if url_foto:
                base_convertida = base_para_nome_arquivo(base_nome)
                id_formatado = str(resposta['id']).zfill(9)
                nome_arquivo = f"{base_convertida}-{id_formatado}.nst"
                grupo = id_formatado[-3:]  # três últimos dígitos

                nome_diretorio = os.path.join('downloads', base_convertida, grupo)
                os.makedirs(nome_diretorio, exist_ok=True)

                caminho_destino = os.path.join(nome_diretorio, nome_arquivo)

                conteudo_foto = download_imagem(url_foto)
                gera_nist_canaime(dados_pessoa=resposta, foto=conteudo_foto, base_nome=base_nome, caminho_destino=caminho_destino)

                logger.info(f"[Base: {base_nome} | Página: {pagina}] Nist {nome_arquivo} salvo em {nome_diretorio}.")
                salvar_ultimo_id(base_nome, int(resposta['id']))
            else:
                logger.info(f"[Base: {base_nome} | Página: {pagina}] Nenhuma foto encontrada para o ID {id_atual}.")
        except requests.HTTPError as e:
            logger.error(f"[Base: {base_nome} | Página: {pagina}] Erro HTTP ao processar ID {id_atual}: {e}")
        except Exception as e:
            logger.error(f"[Base: {base_nome} | Página: {pagina}] Erro ao processar ID {id_atual}: {e}")

        id_atual += 1

    logger.info(f"[Base: {base_nome} | Página: {pagina}] Processamento concluído.")


def main() -> None:
    load_dotenv()

    token = os.getenv('TOKEN')
    usuario = os.getenv('USUARIO')
    senha = os.getenv('SENHA')

    if not all([token, usuario, senha]):
        logger.error("Erro: variáveis de ambiente TOKEN, USUARIO e SENHA não configuradas.")
        return

    config = ler_configuracao_yaml('config.yaml')
    bases = config.get('BASES', {})

    if not bases:
        logger.error("Nenhuma base encontrada no arquivo de configuração.")
        return

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(processar_pagina, token, usuario, senha, base_nome, pagina)
            for base_nome, pagina in bases.items()
        ]

        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Erro ao processar uma base: {e}")


if __name__ == '__main__':
    main()
