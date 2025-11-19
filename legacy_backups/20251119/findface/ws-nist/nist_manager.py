from NIST import NIST
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import object_session
from app import app
from database.models import db, Nist, BaseOrigem, Log, NistFindface, Findface, BaseOrigemFindface
from mitra_toolkit.functions import *
from mitra_toolkit.mitra_toolkit import MitraException, MitraToolkit, PessoaFindface
import traceback
import os
from findface_multi.findface_multi import FindfaceConnection, FindfaceException, FindfaceMulti
from config_app import *
import hashlib
from pathlib import Path
from time import sleep
import shutil
import traceback


def envia_nist_para_findface(nist: Nist, carga_inicial=False)-> dict:
    """
    Envia um objeto Nist para os sistemas Findface associados e cria ou atualiza cartões de identificação.

    Argumentos:
    - nist (Nist): Objeto Nist que será enviado.

    Retorna:
    - Um dicionário contendo os cartões de identificação criados ou atualizados no Findface, se a operação for bem sucedida.
    
    Exceção:
    - TypeError: Se o objeto fornecido não for uma instância de Nist.
    - MitraException: Se ocorrer um erro durante a comunicação com o sistema Findface ou ao processar a adição no banco de dados.

    Observações:
    - A função verifica se o arquivo NIST existe e se o objeto Nist é válido.
    - Para cada Findface relacionado, a função verifica se já existe um cartão associado ao Nist. Se não existir, tenta criar um novo.
    - Utiliza um gerenciador de contexto para garantir que a conexão com o Findface seja fechada apropriadamente após a tentativa de envio.
    - Registra logs correspondentes para cada etapa significativa do processo, incluindo sucesso ou falhas na criação ou atualização dos cartões.
    """

    if not isinstance(nist, Nist):
        db.session.rollback()
        raise TypeError(f"Tipo {type(nist)} inválido para 'nist'. Esperado <class Nist>.")

    if not Path(nist.uri_nist).exists():
        print(f"[envia_nist_para_findface] Arquivo não encontrado: {nist.uri_nist}.")
        return

    # Terceiro passo é enviar o NIST para cada Findface associado à base do Nist (op tipo 2) 
    # Recupera o item NIST
    
    if nist:
        # Instancia PessoaFindface com o nist recebido
        pessoa_ff = nist_to_pessoa_ff(nist.uri_nist, id_nist=nist.id_nist)

        for findface in nist.base_origem.findfaces:
            # Identifica a relação NistFindface
            relacao_nist_findface = NistFindface.query.filter_by(id_nist=nist.id_nist, id_findface=findface.id_findface).first()
            if relacao_nist_findface and relacao_nist_findface.card_id:
                # Se já houver um card na relação, encerra a função
                msg_sucesso = f'Relação NistFindface #{relacao_nist_findface.id_nist_findface} já possui o Card #{relacao_nist_findface.card_id}.'
                # add_log(cd_tipo_log=31, id_origem=relacao_nist_findface.id_nist_findface, ds_log=msg_sucesso)
                print('[nist_manager] ' + msg_sucesso)
            else:
                try:
                    with FindfaceConnection(base_url=findface.url_base, username=FINDFACE_USER, password=FINDFACE_PASSWORD) as findface_connection:
                        findface_multi = FindfaceMulti(findface_connection)
                        mitra_toolkit = MitraToolkit(findface_multi)
                        pessoa_ff.findface = findface_multi

                        msg_erro = None
                        msg_sucesso = None
                        cards = mitra_toolkit.add_pessoa_to_findface(pessoa_ff, carga_inicial=carga_inicial)

                        # Se encontrou um card existente para a pessoa enviada
                        if isinstance(cards, (list, tuple)) and len(cards) > 0:                            
                            card_id = cards[0]["id"]
                            # Adiciona o Log da atualização da relação NistFindface
                            relacao_nist_findface.card_id = card_id
                            db.session.flush()
                            msg_sucesso = f'Relação NistFindface #{relacao_nist_findface.id_nist_findface} atualizada com card #{card_id}'
                            # add_log(cd_tipo_log=22, id_origem=relacao_nist_findface.id_nist_findface, ds_log=msg_sucesso)
                            print('[nist_manager] ' + msg_sucesso)

                            # Adiciona o log de sucesso do cadastro/atualização do NIST para o Findface
                            msg_sucesso = f'Nist #{relacao_nist_findface.id_nist} já existe no Findface "{findface.no_findface}" com Card #{card_id}.'
                            # add_log(cd_tipo_log=31, id_origem=relacao_nist_findface.id_nist_findface, ds_log=msg_sucesso)
                            print('[nist_manager] ' + msg_sucesso)

                        # Se criou um novo card para a pessoa enviada
                        elif isinstance(cards, dict):
                            card_id = cards["id"]
                            # Adiciona o Log da atualização da relação NistFindface
                            relacao_nist_findface.card_id = card_id
                            db.session.flush()
                            msg_sucesso = f'Relação NistFindface #{relacao_nist_findface.id_nist_findface} atualizada com card #{card_id}'
                            # add_log(cd_tipo_log=22, id_origem=relacao_nist_findface.id_nist_findface, ds_log=msg_sucesso)
                            print('[nist_manager] ' + msg_sucesso)
                            
                            # Adiciona o log de sucesso do cadastro/atualização do NIST para o Findface
                            msg_sucesso = f'Nist #{relacao_nist_findface.id_nist} criado no Findface "{findface.no_findface}" com Card #{card_id}.'
                            # add_log(cd_tipo_log=30, id_origem=relacao_nist_findface.id_nist_findface, ds_log=msg_sucesso)
                            print('[nist_manager] ' + msg_sucesso)
                            relacao_nist_findface.card_id = card_id
                            db.session.flush()

                        else:
                            msg_erro = f"Tipo inválido para 'cards'."
                            db.session.rollback()
                            add_log(cd_tipo_log=39, id_origem=relacao_nist_findface.id_nist_findface, ds_log=msg_erro)
                            print('[nist_manager] ' + msg_erro)
                            # raise MitraException(msg_erro)

                    db.session.commit()

                    # Removido devido ao erro: cannot access local variable 'cards' where it is not associated with a value
                    # if cards:                        
                    #     return cards

                except Exception as e:
                    db.session.rollback()
                    move_nists_lidos_com_erro(nist)                    
                    msg_erro = traceback.format_exc()
                    # add_log(cd_tipo_log=39, id_origem=id_origem, ds_log=msg_erro)
                    add_log(cd_tipo_log=39, ds_log=msg_erro)
                    db.session.commit()
                    print('[nist_manager] ' + msg_erro)
                    # raise MitraException(traceback.format_exc())
                        

def add_relacao_nist_findface(id_nist: int) -> None|NistFindface:
    '''
    Adiciona relações entre um objeto Nist e objetos Findface associados.
    
    Argumentos:
    - id_nist (int): Identificador do Nist para o qual as relações serão criadas.

    Retorna:
    - None se não for possível adicionar qualquer relação ou se as relações já existirem.
    - Lista de objetos NistFindface recém-criados se novas relações forem estabelecidas.
    '''

    if not isinstance(id_nist, int):
        db.session.rollback()
        raise TypeError(f'Tipo inválido para id_nist. Esperado int.')
    
    # Recupera o obeto Nist
    nist_item = Nist.query.filter(Nist.id_nist==id_nist).first()
    if nist_item:
        findfaces = nist_item.base_origem.findfaces
    else:
        raise MitraException(f'NIST não encontrado #{id_nist}. ')

    relacoes_criadas = []
    relacoes_existentes = []
    for findface in findfaces:

        relacao_exite = NistFindface.query.filter(NistFindface.id_nist==nist_item.id_nist, NistFindface.id_findface==findface.id_findface).first()
        if relacao_exite:
            msg_sucesso = f'Relação NistFindface #{relacao_exite.id_nist_findface} já existe para Nist #{nist_item.id_nist} e Findface #{findface.id_findface}.'
            # add_log(cd_tipo_log=21, id_origem=relacao_exite.id_nist_findface, ds_log=msg_sucesso)
            print('[nist_manager] ' + msg_sucesso)
            relacoes_existentes.append(relacao_exite)
        else:
            nova_relacao = NistFindface(id_nist=nist_item.id_nist, id_findface=findface.id_findface)
            db.session.add(nova_relacao)
            db.session.flush()
            msg_sucesso = f'Relação NistFindface #{nova_relacao.id_nist_findface} entre Nist #{nist_item.id_nist} e Findface #{findface.id_findface} criada.'
            # add_log(cd_tipo_log=20, id_origem=nova_relacao.id_nist_findface, ds_log=msg_sucesso)            
            print('[nist_manager] ' + msg_sucesso)
            relacoes_criadas.append(nova_relacao)

    if relacoes_existentes:
        print(f'[nist_manager] {len(relacoes_existentes)} relações NistFindface existentes para o Nist #{nist_item.id_nist}.')
    
    if relacoes_criadas:
        print(f'[nist_manager] {len(relacoes_existentes)} relações NistFindface criadas para o Nist #{nist_item.id_nist}.')

    db.session.commit()

    return relacoes_criadas
    

def nist_to_pessoa_ff(nist_filepath:str, id_nist:int|None=None) -> None|PessoaFindface:
    """
    Função que instancia um objeto PessoaFindface a partir de um arquivo NIST.

    Parâmetros:
    nist_filepath: caminho para o arquivo NIST no disco.

    Returno:
    Objeto PessoaFindface ou None
    """

    # Patch necessário para corrigir o caminho absuluto no servidor sdf0990
    # Substitui o caminho absoluto do SO pelo caminho absoluto da aplicação
    if '/mnt/NIST/isilon_old/Sismigra/lidos' in nist_filepath:        
        nist_filepath = nist_filepath.replace('/mnt/NIST/isilon_old/Sismigra/lidos', '/mnt/mitra/nists/pf/sismigra')
    elif '/mnt/NIST/AFIS/Nists_Lidos' in nist_filepath:
        nist_filepath = nist_filepath.replace('/mnt/NIST/AFIS/Nists_Lidos', '/mnt/mitra/nists/pf/sinpa')

    if id_nist and not isinstance(id_nist, int):
        print(f"Tipo {type(id_nist)} inválido para 'id_nist'. Esperado <class int> or None.")
        raise TypeError(f"Tipo {type(id_nist)} inválido para 'id_nist'. Esperado <class int> or None.")
    
    if not nist_filepath:
        print(f"'nist_filepath' não pode ser nulo.")
        raise ValueError(f"'nist_filepath' não pode ser nulo.")

    if not Path(nist_filepath).exists():
        # Salva um log com código 18 contendo o caminho relativo para o NIST
        caminho_relativo_nist = obter_caminho_relativo_nist(nist_filepath)
        if not Log.query.filter_by(ds_log=caminho_relativo_nist).first():
            add_log(cd_tipo_log=18, ds_log=caminho_relativo_nist)
            db.session.commit()
        # raise FileNotFoundError(f"Arquivo Nist não encontrado. '{nist_filepath}'")
        print(f"[envia_para_findface] Arquivo não encontrado. {nist_filepath}.")
        return
        
    # Tenta 5x ler o conteúdo do arquivo Nist
    for i in range(1, 6):
        with open(nist_filepath, 'rb') as f:
            conteudo_nist = io.BytesIO(f.read())        
        if len(conteudo_nist.getvalue()) == 0:
            print(f"[nist_manager] Arquivo NIST vazio. Tentando ler '{nist_filepath}' {i}x...")
            sleep(1)
        else:
            break

    # Se o conteúdo continuar vazio após as 10 tentativas, retorna None
    if not conteudo_nist.getvalue():
        # Salva um log com código 18 contendo o caminho relativo para o NIST
        caminho_relativo_nist = obter_caminho_relativo_nist(nist_filepath)
        if not Log.query.filter_by(ds_log=caminho_relativo_nist).first():
            add_log(cd_tipo_log=18, ds_log=caminho_relativo_nist)
            db.session.commit()
        print(f"[envia_para_findface] Arquivo vazio. {nist_filepath}.")
        return None

        
    # Gera o hash md5 do Nist
    md5_hash = hashlib.md5(conteudo_nist.getvalue()).hexdigest()

    # Instancia PessoaFindface com os dados do NIST
    pessoa_ff = PessoaFindface(findface=None, nist=conteudo_nist.getvalue())

    if pessoa_ff:
        pessoa_ff.md5_hash = md5_hash

        # Se foi passado o id_nist, adiciona no objeto pessoa
        if id_nist:
            pessoa_ff.id_nist = id_nist

        # Obtem o caminho relativo do arquivo nist em relação ao diretório raiz da aplicação
        pessoa_ff.uri_nist = obter_caminho_relativo_nist(nist_filepath)

        # Verifica se a Base de Origem (PessoaFindface.lista) consta no banco de dados e obtém o seu registro.
        base_origem = BaseOrigem.query.filter_by(no_base_origem=pessoa_ff.lista).first()
        
        if not base_origem:
            db.session.rollback()
            msg_erro = f"Base de origem '{pessoa_ff.lista}' desconhecida. Contate o administrador <leonardo.lad@pf.gov.br>'"
            add_log(cd_tipo_log=19, ds_log=msg_erro)
            db.session.commit()
            raise MitraException('[add_nist]' + msg_erro)

        # Atualiza PessoaFindface com o status ativo/inativo de acordo com a Base de Origem
        pessoa_ff.ativo = base_origem.ativo
        # Adiciona à PessoaFindface o ID da Base de Origem
        pessoa_ff.id_base_origem = base_origem.id_base_origem

        return pessoa_ff


def obter_caminho_relativo_nist(nist_filepath:str) -> str:
    """
    Calcula o caminho relativo de um arquivo NIST em relação ao diretório raiz da aplicação.

    Argumentos:
    - nist_filepath (str): Caminho absoluto do arquivo NIST.

    Retorna:
    - str: Caminho relativo do arquivo NIST em relação ao diretório raiz da aplicação.
    
    Observações:
    - Se o arquivo não estiver no subdiretório do diretório raiz da aplicação, retorna o caminho absoluto.
    - Esta função pode ser útil para armazenar caminhos de arquivos de forma relativa no banco de dados ou para referências internas.
    """    
    try:
        nist_relative_path = Path(nist_filepath).relative_to(APP_DIR)
    except ValueError:
        nist_relative_path = nist_filepath

    return str(nist_relative_path)


def obter_caminho_absoluto_nist(caminho_relativo_nist:str) -> str:
    """
    Calcula o caminho absoluto de um arquivo NIST a partir de seu caminho relativo em relação ao diretório raiz da aplicação.

    Argumentos:
    - caminho_relativo_nist (str): Caminho relativo do arquivo NIST em relação ao diretório raiz da aplicação.

    Retorna:
    - str: Caminho absoluto do arquivo NIST.
    
    Observações:
    - Esta função é útil para resolver o caminho absoluto de arquivos NIST especificados relativamente à localização do script principal da aplicação.
    """

    nist_absolut_path = APP_DIR / str(caminho_relativo_nist)
    return str(nist_absolut_path)


def load_nist_object_from_uri(nist_filepath: str) -> Nist:
    """
    Carrega e cria um objeto Nist a partir de um arquivo NIST especificado pelo caminho do arquivo.

    Argumentos:
    - nist_filepath (str): Caminho do arquivo NIST.

    Retorna:
    - Nist: Objeto Nist criado a partir das informações do arquivo NIST se o processo for bem-sucedido.
    
    Levanta:
    - TypeError: Se o tipo de 'nist_filepath' não for uma string.
    - MitraException: Se ocorrerem erros ao carregar a Base de Origem ou ao converter o arquivo NIST para o objeto Nist.
    
    Observações:
    - A função tenta converter um arquivo NIST em um objeto PessoaFindface e, posteriormente, em um objeto Nist.
    - Registra um log de erro e faz rollback da transação se encontrar qualquer problema durante a conversão ou recuperação da Base de Origem.
    - Em caso de sucesso, retorna o objeto Nist correspondente; caso contrário, pode retornar None se não houver erros críticos que exijam exceções.
    """

    if not isinstance(nist_filepath, str):
        raise TypeError(f"Tipo {type(nist_filepath)} inválido para 'nist_filepath'. Esperado <class str>.")

    # Instancia um objeto PessoaFindface com o NIST informado
    try:
        pessoa_ff = nist_to_pessoa_ff(nist_filepath)
    except:
        msg_erro = traceback.format_exc()
        add_log(cd_tipo_log=19, ds_log=msg_erro)
        db.session.commit()
        print(f"[nist_manager] ", msg_erro)
        pessoa_ff = None
    
    if pessoa_ff:
        # Recuperao ID da Base de Origem
        base_origem = BaseOrigem.query.filter_by(no_base_origem=pessoa_ff.lista).first()
        if not base_origem:
            db.session.rollback()
            msg_erro = f"Base de Origem '{pessoa_ff.lista}' inválida. Contate o administrador <leonardo.lad@pf.gov.br>"
            add_log(cd_tipo_log=19, ds_log=msg_erro)
            db.session.commit()
            raise MitraException(msg_erro)
       
        nist = Nist(
            no_pessoa=pessoa_ff.nome,
            no_social=pessoa_ff.nome_social,
            dt_nascimento=pessoa_ff.nascimento,
            tp_sexo=pessoa_ff.sexo,
            no_mae=pessoa_ff.mae,
            no_pai=pessoa_ff.pai,
            ds_naturalidade=pessoa_ff.naturalidade,
            ds_pais_nacionalidade=pessoa_ff.nacionalidade,
            nr_cpf=pessoa_ff.cpf,
            nr_rnm=pessoa_ff.rnm,
            nr_passaporte=pessoa_ff.passaporte,
            nr_documento=pessoa_ff.documento,
            uri_nist=pessoa_ff.uri_nist,
            id_base_origem=base_origem.id_base_origem,
            ativo = pessoa_ff.ativo,
            md5_hash = pessoa_ff.md5_hash
        )

        return nist
    else:
        pass
        # db.session.rollback()
        # msg_erro = f"{traceback.format_exc()}. URI: {nist_filepath}."
        # add_log(cd_tipo_log=19, id_origem=None, ds_log=msg_erro)
        # db.session.commit()


def obter_novas_relacoes_nist_findface_por_nist(nist: Nist) -> None|list:
    """
    Identifica e cria novas relações entre um objeto Nist e sistemas Findface associados à sua base de origem.

    Argumentos:
    - nist (Nist): Objeto Nist a partir do qual as relações serão exploradas e potencialmente criadas.

    Retorna:
    - list: Lista de novas relações NistFindface que precisam ser criadas se existirem novas.
    - None: Se não existirem novas relações a serem criadas.

    Levanta:
    - TypeError: Se o objeto fornecido não for uma instância de Nist.
    
    Observações:
    - A função verifica a existência de relações prévias entre o Nist e cada Findface associado.
    - Se a relação já existir, ela é adicionada à lista de relações existentes, mas não é retornada.
    - Se a relação não existir, é criada uma nova instância de NistFindface e adicionada à lista de novas relações a serem potencialmente criadas.
    - A função retorna apenas as novas relações que necessitam ser adicionadas ao banco de dados.
    """

    if not isinstance(nist, Nist):
        db.session.rollback()
        raise TypeError(f"Tipo {type(nist)} inválido para 'id_nist'. Esperado <class Nist>.")

    lista_novas_relacoes = []
    lista_relacoes_existentes = []
    findfaces = nist.base_origem.findfaces
    for findface in findfaces:

        relacao_existente = NistFindface.query.filter(NistFindface.id_nist==nist.id_nist, NistFindface.id_findface==findface.id_findface).first()
        if relacao_existente:
            if relacao_existente not in lista_relacoes_existentes:
                lista_relacoes_existentes.append(relacao_existente)
                # print(f"[nist_manager] Nist #{nist.id_nist} já está vinculado ao Findface '{findface.no_findface}'.")
        else:
            nova_relacao = NistFindface(id_nist=nist.id_nist, id_findface=findface.id_findface)
            if nova_relacao not in lista_novas_relacoes:
                lista_novas_relacoes.append(nova_relacao)
                # print(f"[nist_manager] Nist #{nist.id_nist} precisa ser vinculado ao Findface '{findface.no_findface}'.")

    if lista_relacoes_existentes:
        pass
    
    if lista_novas_relacoes:
        pass            

    return lista_novas_relacoes


# def obter_todas_as_novas_relacoes_nist_findface() -> list|None:
#     """
#     Identifica novas relações potenciais entre registros Nist e sistemas Findface que ainda não estão vinculados diretamente.

#     Argumentos:
#     - 

#     Retorna:
#     - list: Lista de objetos NistFindface representando novas relações que precisam ser estabelecidas.

#     Observações:
#     - A função percorre todos os registros de Findface e, para cada um, identifica as BasesOrigem relacionadas.
#     - Para cada BaseOrigem, identifica os registros Nist que não possuem uma relação direta com o Findface específico.
#     - Utiliza uma consulta SQL com junções e filtros para identificar relações faltantes.
#     - Retorna um conjunto convertido em lista para evitar duplicatas e garantir que apenas novas relações sejam consideradas.
#     """

#     result = set()
#     # Percorre todos os registros de Findface
#     findfaces = Findface.query.all()
    
#     for findface in findfaces:
#         # Para cada Findface, identificar as BasesOrigem relacionadas
#         bases_origem = BaseOrigem.query \
#             .join(BaseOrigemFindface, BaseOrigemFindface.id_base_origem == BaseOrigem.id_base_origem) \
#             .filter(BaseOrigemFindface.id_findface == findface.id_findface) \
#             .all()
        
#         for base_origem in bases_origem:
#             # Para cada BaseOrigem, encontrar todos os Nists relacionados que não têm uma ligação direta com o Findface
#             nist_query = db.session.query(Nist.id_nist) \
#                 .filter(Nist.id_base_origem == base_origem.id_base_origem) \
#                 .outerjoin(NistFindface, NistFindface.id_nist == Nist.id_nist) \
#                 .filter(NistFindface.id_findface == None)

#             nist_id_list = [nist_id[0] for nist_id in nist_query.all()]
            
#             nist_findface_set = set()
#             for nist_id in nist_id_list:
#                 nist_findface = NistFindface(id_nist=nist_id, id_findface=findface.id_findface)
#                 nist_findface_set.add(nist_findface)
#                 result.add(nist_findface)

#             db.session.add_all(nist_findface_set)
#             db.session.commit()
#             print(f"[adiciona_novos_relacionamentos] {len(nist_findface_set)} relacionamentos criados no banco para a base {base_origem.no_base_origem}.")

#     return list(result)


def obter_todas_as_novas_relacoes_nist_findface() -> list | None:
    """
    Identifica novas relações potenciais entre registros Nist e sistemas Findface que ainda não estão vinculados diretamente.

    Retorna:
    - list: Lista de objetos NistFindface representando novas relações que precisam ser estabelecidas.

    Observações:
    - Processa os registros de forma paginada para evitar estouro de memória.
    """

    findfaces = Findface.query.all()  # Obtém todos os registros Findface

    for findface in findfaces:
        # Obtém as BasesOrigem relacionadas ao Findface
        bases_origem = BaseOrigem.query \
            .join(BaseOrigemFindface, BaseOrigemFindface.id_base_origem == BaseOrigem.id_base_origem) \
            .filter(BaseOrigemFindface.id_findface == findface.id_findface) \
            .all()

        for base_origem in bases_origem:
            total_adicionado_na_base = 0
            # Processa os Nists em lotes de 100 registros por vez
            offset = 0
            batch_size = 100
            while True:
                # Consulta com limite e deslocamento para paginação
                nist_query = db.session.query(Nist.id_nist) \
                    .filter(Nist.id_base_origem == base_origem.id_base_origem) \
                    .outerjoin(NistFindface, NistFindface.id_nist == Nist.id_nist) \
                    .filter(NistFindface.id_findface == None) \
                    .limit(batch_size) \
                    .offset(offset) \
                    .all()

                if not nist_query:
                    # Se não houver mais registros, sair do loop
                    break

                # Adiciona os relacionamentos para o lote atual
                result = set()
                for nist_id_row in nist_query:
                    nist_id = nist_id_row[0]  # Extrai o ID do Nist
                    nist_findface = NistFindface(id_nist=nist_id, id_findface=findface.id_findface)
                    result.add(nist_findface)

                # Incrementa o deslocamento para o próximo lote
                offset += batch_size

                # Salva os novos relacionamentos no banco após processar todos os lotes de uma BaseOrigem
                db.session.add_all(result)
                db.session.commit()
                
                total_adicionado_na_base += len(result)
                
                result.clear()  # Limpa o conjunto para o próximo Findface/BaseOrigem
                

            print(f"[adiciona_novos_relacionamentos] {total_adicionado_na_base} relacionamentos criados no banco para a base {base_origem.no_base_origem}.")


    return list(result)


def find_nists_without_findface_link(limit:int=None) -> list:
    """
    Busca registros Nist que não estão vinculados a um Findface correspondente, considerando a base de origem associada.

    Argumentos:
    - limit (int, opcional): Limita o número de Nists a serem retornados.

    Retorna:
    - list: Lista de registros Nist que não possuem vínculo direto com um Findface.

    Observações:
    - A função percorre todos os registros de Findface disponíveis.
    - Para cada Findface, identifica as BasesOrigem que estão vinculadas a ele.
    - Para cada BaseOrigem, a função busca registros Nist que não possuem um link direto com qualquer Findface associado a essa base.
    - A busca é feita usando uma consulta SQL que inclui junções e filtros para identificar Nists sem links.
    - Se um limite é fornecido, a função interrompe a busca assim que este limite é atingido, garantindo que não mais do que o número especificado de Nists seja retornado.
    - Os resultados são desduplicados antes de serem retornados para evitar a repetição de registros Nist na lista final.
    """

    result = []
    # Percorre todos os registros de Findface
    findfaces = Findface.query.all()
    
    for findface in findfaces:
        # Para cada Findface, identificar as BasesOrigem relacionadas
        bases_origem = BaseOrigem.query \
            .join(BaseOrigemFindface, BaseOrigemFindface.id_base_origem == BaseOrigem.id_base_origem) \
            .filter(BaseOrigemFindface.id_findface == findface.id_findface) \
            .all()
        
        for base_origem in bases_origem:
            # Para cada BaseOrigem, encontrar todos os Nists relacionados que não têm uma ligação direta com o Findface
            nist_query = Nist.query \
                .filter(Nist.id_base_origem == base_origem.id_base_origem) \
                .outerjoin(NistFindface, NistFindface.id_nist == Nist.id_nist) \
                .filter(or_(NistFindface.id_findface == None, NistFindface.id_findface != findface.id_findface))
            
            if limit is not None and len(result) < limit:
                # Limita o número de resultados se um limite foi definido e ainda não foi alcançado
                nists = nist_query.limit(limit - len(result)).all()
            else:
                nists = nist_query.all()
            
            result.extend(nists)
            if limit is not None and len(result) >= limit:
                # Para o processo se o limite for atingido
                return list(set(result[:limit]))
    
    return list(set(result))  # Remove os duplicados


# def obtem_todos_os_nists_com_findface_mas_sem_cardid(limit:int=None) -> list:
#     """
#     Recupera registros Nist que estão vinculados a um Findface, mas não possuem um card_id associado.

#     Argumentos:
#     - limit (int, opcional): Limita o número de registros Nist a serem retornados.

#     Retorna:
#     - list: Lista de registros Nist que têm uma relação com Findface onde o card_id é nulo.

#     Observações:
#     - A função executa uma consulta que junta os registros Nist com suas respectivas relações NistFindface,
#       filtrando por aqueles onde o card_id é nulo.
#     - Isso pode ser útil para identificar registros Nist que precisam de atualização ou revisão na relação com Findface.
#     - Se um limite é especificado, apenas essa quantidade de registros Nist será retornada.
#     - Um log é gerado para informar quantos registros Nist foram encontrados sem card_id.
#     """
#     # Consulta para Nists que têm uma relação com Findface onde card_id é nulo em NistFindface
#     nist_query = Nist.query \
#         .join(NistFindface, Nist.id_nist == NistFindface.id_nist) \
#         .filter(NistFindface.card_id == None)
    
#     if limit is not None:
#         nists_with_null_card_id = nist_query.limit(limit).all()
#     else:
#         nists_with_null_card_id = nist_query.all()

#     print(f"[nist_manager] {len(nists_with_null_card_id)} NISTs sem card_id.")

#     return nists_with_null_card_id


def obtem_todos_os_nists_com_findface_mas_sem_cardid(limit: int = None, offset: int = None) -> list:
    """
    Recupera registros Nist que estão vinculados a um Findface, mas não possuem um card_id associado.

    Argumentos:
    - limit (int, opcional): Limita o número de registros Nist a serem retornados.
    - offset (int, opcional): Especifica o deslocamento inicial na lista de resultados.

    Retorna:
    - list: Lista de registros Nist que têm uma relação com Findface onde o card_id é nulo.

    Observações:
    - A função executa uma consulta que junta os registros Nist com suas respectivas relações NistFindface,
      filtrando por aqueles onde o card_id é nulo.
    - Isso pode ser útil para identificar registros Nist que precisam de atualização ou revisão na relação com Findface.
    - Se um limite e/ou um offset são especificados, a consulta será ajustada para retornar apenas essa quantidade de registros
      a partir do deslocamento especificado.
    - Um log é gerado para informar quantos registros Nist foram encontrados sem card_id.
    """
    # # Consulta para Nists que têm uma relação com Findface onde card_id é nulo em NistFindface
    # nist_query = Nist.query \
    #     .join(NistFindface, Nist.id_nist == NistFindface.id_nist) \
    #     .filter(NistFindface.card_id == None)  
    # Construção da query base

    # Consulta para Nists que têm uma relação com Findface onde card_id é nulo em NistFindface
    nist_query = Nist.query \
        .join(NistFindface, Nist.id_nist == NistFindface.id_nist) \
        .filter(NistFindface.card_id == None)  # Filtro fixo
        
    # Aplicando offset se fornecido
    if offset is not None:
        nist_query = nist_query.offset(offset)
    
    # Aplicando limit se fornecido
    if limit is not None:
        nist_query = nist_query.limit(limit)
    
    nists_with_null_card_id = nist_query.all()
    print(f"[nist_manager] {len(nists_with_null_card_id)} NISTs sem card_id.")

    return nists_with_null_card_id


def add_nist_to_db(new_nist: Nist) -> Nist|None:
    """
    Adiciona um novo registro Nist ao banco de dados ou retorna um existente com base na correspondência do hash MD5.

    Argumentos:
    - new_nist (Nist): Objeto Nist a ser adicionado ao banco de dados.

    Retorna:
    - Nist: O objeto Nist existente no banco de dados se já houver uma entrada com o mesmo hash MD5.
    - Nist: O novo objeto Nist adicionado ao banco de dados se não houver correspondência.
    - None: Em caso de falha durante a adição ao banco.

    Levanta:
    - TypeError: Se o objeto fornecido não for uma instância de Nist.

    Observações:
    - A função primeiro verifica se já existe um registro Nist com o mesmo hash MD5 no banco de dados.
    - Se existir, retorna esse registro e loga a ocorrência.
    - Se não, tenta adicionar o novo Nist ao banco de dados, registrando o sucesso da operação ou falha com um rollback e log correspondente.
    """

    if not isinstance(new_nist, Nist):
        raise TypeError(f"Tipo {type(new_nist)} inválido para 'nist'. Esperado <class Nist>.")

    nist_existente = Nist.query.filter_by(md5_hash=new_nist.md5_hash).first()
    if nist_existente:
        move_nists_lidos(new_nist)
        # msg_sucesso = f"[nist_manager] Nist já cadastrado. Hash MD5: {new_nist.md5_hash}."            
        # add_log(cd_tipo_log=11, ds_log=msg_sucesso)
        # print(msg_sucesso)
        return nist_existente
    else:
        try:
            db.session.add(new_nist)
            db.session.flush()
            msg_sucesso = f"Nist #{new_nist.id_nist} cadastrado no banco com sucesso. URI: {new_nist.uri_nist}."
            # add_log(cd_tipo_log=10, id_origem=new_nist.id_nist, ds_log=msg_sucesso)
            db.session.commit()
            print('[nist_manager]', msg_sucesso)
            move_nists_lidos(new_nist)
            return new_nist
        except:
            db.session.rollback()
            msg_erro = traceback.format_exc()
            add_log(cd_tipo_log=19, ds_log=msg_erro)
            print(msg_erro)
            return None


def verificar_link_simbolico(caminho):
    path = Path(caminho)
    for part in path.parents:
        if part.is_symlink():
            return True
    return path.is_symlink()


def move_nists_lidos(nist: Nist) -> str|None:

    if not isinstance(nist, Nist):
        raise TypeError(f"Tipo {type(nist)} inválido para 'nist'. Esperado '<Nist>'.")

    # Caminho original do arquivo
    caminho_original = Path(nist.uri_nist)

    # # Se o caminho contiver 'nists_lidos', o NIST já foi processado. Retorna None
    # if 'nists_lidos' in str(caminho_original):
    #     print(f"Nist já movido para destino. {str(caminho_original)}")
    #     return None

    partes = list(caminho_original.parts)    
    # Substitui o terceiro subdiretório
    if 'nists' in partes:
        index = partes.index('nists')
        partes[index] = 'nists_lidos'    
    novo_caminho = Path(*partes)

    # Caminho de destino do arquivo
    caminho_destino = novo_caminho

    try:
        # Criando diretórios de destino, se não existirem
        caminho_destino.parent.mkdir(parents=True, exist_ok=True)

        # Alterando o caminho do nist no banco de dados
        nist.uri_nist = str(novo_caminho)
        db.session.flush()

        try:
            if not caminho_destino.exists():
                # Move o arquivo para o novo destino
                shutil.move(str(caminho_original), str(caminho_destino))
                print(f'Nist movido para: {str(novo_caminho)}')
            else:
                # print(f'Arquivo já existe em: {str(caminho_destino)}')
                caminho_original.unlink()  # This deletes the original file
                print(f"Arquivo já existe no destino. Removido. Arquivo: '{str(caminho_original)}'")
                
        except PermissionError as e:
            # Copia o arquivo para o novo destino
            shutil.copy2(caminho_original, caminho_destino)
            print(f'[move_nists_lidos] Nist copiado para: {str(novo_caminho)}') 
        except FileNotFoundError as e:
            print(f'[move_nists_lidos] Arquivo não encontrado: {e}')
        except Exception as e:
            print(traceback.format_exec())

    except Exception as e:
        db.session.rollback()
    
    db.session.commit()


def add_nist_to_db_by_uri(nist_filepath: str) -> Nist|None:
    """
    Adiciona um registro Nist ao banco de dados a partir de um caminho de arquivo NIST, evitando duplicidades baseadas no caminho do arquivo.

    Argumentos:
    - nist_filepath (str): Caminho do arquivo NIST.

    Retorna:
    - Nist: Objeto Nist adicionado ao banco de dados.
    - None: Se o NIST já está cadastrado ou se não foi possível carregar ou adicionar o objeto Nist.

    Observações:
    - A função primeiro verifica se um Nist com o mesmo caminho do arquivo já existe no banco de dados.
    - Se o registro já existe, uma mensagem é exibida indicando que o NIST já está cadastrado e a função retorna None.
    - Se não existir, a função tenta carregar o objeto Nist do caminho do arquivo especificado.
    - Se o objeto Nist é carregado com sucesso, ele é passado para a função `add_nist_to_db` para ser adicionado ao banco.
    - A função trata internamente a verificação de duplicidade e o carregamento do arquivo NIST, encapsulando os detalhes de verificação e adição.
    """

    nist = Nist.query.filter_by(uri_nist=nist_filepath).first()
    if nist:
        # print(f"NIST já cadastrado. URI: '{nist_filepath}'.")
        # move_nists_lidos(nist)
        return
        
    new_nist = load_nist_object_from_uri(nist_filepath)

    if new_nist:
        return add_nist_to_db(new_nist)


def add_novas_relacoes_por_nist(nist: Nist)-> list|None:
    """
    Adiciona novas relações entre um objeto Nist e sistemas Findface no banco de dados, caso não existam previamente.

    Argumentos:
    - nist (Nist): Objeto Nist para o qual as novas relações com Findface serão adicionadas.

    Retorna:
    - list: Lista das novas relações NistFindface adicionadas ao banco de dados.
    - None: Se não houver novas relações a serem adicionadas.

    Levanta:
    - TypeError: Se o objeto fornecido não for uma instância de Nist.

    Observações:
    - A função verifica primeiro a validade do objeto Nist.
    - Em seguida, utiliza a função `obter_novas_relacoes_nist_findface_por_nist` para identificar possíveis novas relações entre o Nist fornecido e sistemas Findface.
    - Se forem identificadas novas relações, estas são adicionadas ao banco de dados e um log é gerado para cada nova relação adicionada.
    - A função é útil para garantir que todas as relações necessárias sejam estabelecidas sem duplicidade, melhorando a integração entre os registros Nist e os sistemas Findface.
    """    
    
    if not isinstance(nist, Nist):
        raise TypeError(f"Tipo {type(nist)} inválido para 'nist'. Esperado <class Nist>.")

    novas_relacoes = obter_novas_relacoes_nist_findface_por_nist(nist)
    if novas_relacoes:
        db.session.add_all(novas_relacoes)
        db.session.commit()
        print(f"{len(novas_relacoes)} novas relações criadas para o NIST #{nist.id_nist}")
        # for relacao in novas_relacoes:
        #     findface = Findface.query.filter_by(id_findface=relacao.id_findface).first()
        #     msg_sucesso = f"Relação NistFindface #{relacao.id_nist_findface} criada entre Nist #{nist.id_nist} e Findface '{findface.no_findface}'."
        #     # add_log(cd_tipo_log=20, id_origem=relacao.id_nist_findface, ds_log=msg_sucesso)
        #     print(f"[add_nist] " + msg_sucesso)

    return novas_relacoes


def add_nist(nist_filepath: str) -> dict|None:
    '''
    Adiciona um NIST ao banco de dados e cria relações NistFindface para o mesmo,
    além de enviar os dados para o sistema Findface.
    
    Argumentos:
    - nist_filepath (str): Caminho do arquivo NIST a ser processado e adicionado.
    
    Retorna:
    - Lista de cartões de identificação criados no Findface se bem sucedido.
    - None caso contrário.
    '''

    if not nist_filepath:
        raise ValueError(r'Caminho para o arquivo NIST obrigatório.')

    with app.app_context() as context:

        # Primeiro passo é cadastrar o Nist no banco (op tipo 10), se não existe ainda
        nist = add_nist_to_db_by_uri(nist_filepath)

        if nist:
            # Segundo passo é criar as relações NistFindface para o Nist criado
            novas_relacoes = add_novas_relacoes_por_nist(nist)

            # Ultimo passo é cadastrar o NIST no(s) Findface(s) relacionados
            cards = envia_nist_para_findface(nist)

            if cards:
                return cards
        else:
            pass
            # print(f"Nenhum NIST adicionado ao banco.")


def add_log(cd_tipo_log:int, id_origem:int=None, ds_log:str=None):
    '''
    Registra um log no banco de dados com informações sobre operações realizadas.
    
    Argumentos:
    - cd_tipo_log (int): Código do tipo de log.
    - id_origem (int, opcional): Identificador de origem para o log.
    - ds_log (str, opcional): Descrição detalhada do log.
    
    Não retorna valores.
    '''
    new_log = Log(cd_tipo_log=cd_tipo_log, id_origem=id_origem, ds_log=ds_log)
    db.session.add(new_log)        
    db.session.flush()


def move_nists_lidos_com_erro(nist: Nist) -> str|None:

    if not isinstance(nist, Nist):
        raise TypeError(f"Tipo {type(nist)} inválido para 'nist'. Esperado '<Nist>'.")

    # Caminho original do arquivo
    caminho_original = Path(nist.uri_nist)

    # # Se o caminho contiver 'nists_lidos', o NIST já foi processado. Retorna None
    # if 'nists_lidos' in str(caminho_original):
    #     print(f"Nist já movido para destino. {str(caminho_original)}")
    #     return None

    partes = list(caminho_original.parts)    
    # Substitui o terceiro subdiretório
    if 'nists_lidos' in partes:
        index = partes.index('nists_lidos')
        partes[index] = 'nists_lidos_com_erro'    
    else:
        raise Exception("Caminho do nist inválido", nist.uri_nist)
    
    novo_caminho = Path(*partes)

    # Caminho de destino do arquivo
    caminho_destino = novo_caminho

    try:
        # Criando diretórios de destino, se não existirem
        caminho_destino.parent.mkdir(parents=True, exist_ok=True)

        # Alterando o caminho do nist no banco de dados
        nist.uri_nist = str(novo_caminho)
        db.session.flush()

        try:
            if not caminho_destino.exists():
                # Move o arquivo para o novo destino
                shutil.move(str(caminho_original), str(caminho_destino))
                print(f'Nist movido para: {str(novo_caminho)}')
                db.session.commit()
            else:
                # print(f'Arquivo já existe em: {str(caminho_destino)}')
                caminho_original.unlink()  # This deletes the original file
                print(f"Arquivo já existe no destino. Removido. Arquivo: '{str(caminho_original)}'")
                
        except PermissionError as e:
            # Copia o arquivo para o novo destino
            shutil.copy2(caminho_original, caminho_destino)
            print(f'[move_nists_lidos_com_erro] Nist copiado para: {str(novo_caminho)}')
            db.session.commit()
        except FileNotFoundError as e:
            print(f'[move_nists_lidos_com_erro] Arquivo não encontrado: {e}')
        except Exception as e:
            print(traceback.format_exec())

    except Exception as e:
        db.session.rollback()
    
    db.session.commit()


if __name__ == '__main__':

    # CASA
    # nist_filepath = r'amostras\outros\JuliaRoberts-pf-sinpa.nst'
    
    # TRABALHO
    nist_filepath = r'nists\ap\civil\2024-04-19\5501967069961322021681.nst'

    card = add_nist(nist_filepath)
    if card:
        print(card)
