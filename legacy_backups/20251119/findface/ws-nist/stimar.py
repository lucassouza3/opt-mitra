import oracledb
from config_app import *
from sqlalchemy import func, or_, and_, func
from sqlalchemy.orm import aliased
from sqlalchemy.exc import IntegrityError
from database.models import *
from app import app
from datetime import datetime, timedelta
from mitra_toolkit.mitra_toolkit import PessoaFindface, MitraToolkit, MitraException
from findface_multi.findface_multi import FindfaceConnection, FindfaceException, FindfaceMulti
from nist_manager import add_log, move_nists_lidos_com_erro
import traceback
from threader import Threader
from concurrent.futures import ThreadPoolExecutor
from typing import List, Tuple, Optional
import os
from funcoes_uteis import calcular_diferenca_tempo

def obtem_dt_ultima_atualizacao_stimar():
    dt_ultima_atualizacao_stimar = db.session.query(func.max(Alerta.dt_download)).scalar()

    if not dt_ultima_atualizacao_stimar:
        dt_ultima_atualizacao_stimar = datetime(1970, 1, 1, 0, 0, 0)

    return dt_ultima_atualizacao_stimar


def download_alertas_stimar(dt_ultimo_download):
    # Conecta ao banco Oracle
    ORACLE_CONNECTION = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASSWORD,
                        dsn=ORACLE_DSN)

    patch = ''
    if dt_ultimo_download == datetime(1970, 1, 1, 0, 0, 0):
        # Patch para buscar apenas os alertas ativos na primeira carga
        patch = f'AND tara.TP_STATUS IN (1, 4) '

    # Converte Datetime para formato Oracle texto com 3 casas deccimais na fração de segundo
    dt_ultimo_download = dt_ultimo_download.strftime(r'%Y-%m-%d %H:%M:%S.%f')  # Truncate the last three digits to match FF6 precision
    # print('data oracle', dt_ultimo_download)

    #
    # Obtem novos alertas do STIMAR
    #
    print(f'[stimar] Oracle version: {ORACLE_CONNECTION.version}')
    print(f'[stimar] Obtendo novas restrições do STIMAR...')

    with ORACLE_CONNECTION.cursor() as cursor:

        placehold = {
            'dt_ultimo_download': dt_ultimo_download
        }

        sql = f"""
                SELECT 
                    tara.SQ_ALERTA_RESTRICAO AS SQ_ALERTA_RESTRICAO,  
                    tara.SQ_TIPO_ALERTA_RESTRICAO AS SQ_TIPO_ALERTA_RESTRICAO,
                    tara.TP_STATUS AS TP_STATUS,
                    tq.NO_QUALIFICADO AS NO_QUALIFICADO,
                    TO_CHAR(tq.DT_NASCIMENTO, 'YYYY-MM-DD') AS DT_NASCIMENTO,
                    tq.NO_MAE AS NO_MAE, 
                    tq.NO_PAI AS NO_PAI, 
                    tq.NR_CPF AS NR_CPF, 
                    TO_CHAR(tara.DT_ATUALIZACAO, 'YYYY-MM-DD HH24:MI:SS') AS DT_ATUALIZACAO_ALERTA_RESTRICAO,
                    TO_CHAR(tq.DT_ATUALIZACAO, 'YYYY-MM-DD HH24:MI:SS') AS DT_ATUALIZACAO_QUALIFICADO,
                    TO_CHAR(tara.NR_MANDADO_PRISAO) AS NR_MANDADO_PRISAO,                                 
                    TO_CHAR(CURRENT_TIMESTAMP, 'YYYY-MM-DD HH24:MI:SS.FF6') AS DT_DOWNLOAD                
                FROM ASTIMAR100.TB_ALERTA_RESTRICAO tara 
                JOIN ASTIMAR100.TB_QUALIFICADO tq ON tara.SQ_QUALIFICADO = tq.SQ_QUALIFICADO  
                WHERE
                    tara.SQ_TIPO_ALERTA_RESTRICAO IN (4, 7, 9, 13)
                    AND ( tara.DT_ATUALIZACAO > TO_TIMESTAMP(:dt_ultimo_download, 'YYYY-MM-DD HH24:MI:SS.FF6') OR tq.DT_ATUALIZACAO > TO_TIMESTAMP(:dt_ultimo_download, 'YYYY-MM-DD HH24:MI:SS.FF6') )
                    AND ( tq.NR_CPF IS NOT NULL OR 
                    (tq.DT_NASCIMENTO IS NOT NULL AND tq.NO_MAE IS NOT NULL) OR (tq.DT_NASCIMENTO IS NOT NULL AND tq.NO_PAI IS NOT NULL) )
                    {patch}
                """
        rows = cursor.execute(sql, placehold).fetchall()
        print(f'[stimar] {len(rows)} novas restrições encontradas no STIMAR.')

        novos_alertas = []        
        for row in rows:
            # Formata o Número do Mandado de Prisão
            bnmp=row[10]
            if not str(bnmp).isdigit():
                bnmp = None

            novo_alerta = Alerta(
                sq_alerta_restricao=row[0],
                sq_tipo_alerta_restricao=row[1],
                tp_status=row[2],
                no_qualificado=row[3],
                dt_nascimento=row[4],
                no_mae=row[5],
                no_pai=row[6],
                nr_cpf=row[7],
                dt_atualizacao_alerta_restricao=row[8],
                dt_atualizacao_qualificado=row[9],
                nr_mandado_prisao=bnmp,
                dt_download=row[11]
            )
            novos_alertas.append(novo_alerta)

        if novos_alertas:
            print("[stimar] Salvando as novas restrições no banco de dados...")
            db.session.add_all(novos_alertas)
            db.session.commit()
            # print("[stimar] Finalizado!")

    # Fecha a conexão Oracle
    ORACLE_CONNECTION.close()


def alerta_ja_existe(id_alerta, id_nist):
    """
    Função que verifica se já existe um alerta na tabela tb_alerta_nist_findface
    
    Parâmetros:
    - id_nist (int): id correspondente ao registro na tabela tb_nist
    - id_alerta (int): id correspondente ao registro na tabela tb_alerta

    Retorno:
    - True
    - False
    """
    result = AlertaNist.query.filter(AlertaNist.id_nist==id_nist, AlertaNist.id_alerta==id_alerta).first()        
    if result:
        return True
    else:
        return False


def get_most_filled_nist(lista_nists):
    max_filled = None
    max_filled_count = -1

    for nist in lista_nists:
        # Count the number of non-null/non-default fields for each Nist object
        filled_count = sum([1 for value in vars(nist).values() if value is not None and value != "" and not callable(value)])
        
        # Update the max_filled if the current object has more filled fields
        if filled_count > max_filled_count:
            max_filled = nist
            max_filled_count = filled_count

    return max_filled


# def obtem_lista_com_novos_alertas() -> tuple:
#     """
#     Função compara os dados pessoais (nome + data de nascimento + nome da mae|pai) ou cpf na tabela
#     tb_alerta e tb_nist em busca de pessoas com alerta ou restrição (match). Caso encontre,
#     retorna uma lista contendo tuplas com os objetos Alerta e Nist.

#     Parâmetros:
#     - Nenhum

#     Retorno:
#     - lista contendo tuplas com os objetos Alerta e Nist ou None.
#     """
#     results = Alerta.query.join(Nist, or_(
#         and_(
#             Alerta.nr_cpf == Nist.nr_cpf,
#             Alerta.nr_cpf != None,  # Ensure CPF is not None
#             Nist.nr_cpf != None,  # Ensure CPF is not None
#         ),
#         and_(
#             Alerta.no_qualificado == Nist.no_pessoa,
#             Alerta.dt_nascimento == Nist.dt_nascimento,
#             Alerta.no_mae == Nist.no_mae,
#             Alerta.no_qualificado != None,  # Ensure the name is not None
#             Alerta.dt_nascimento != None,  # Ensure the DOB is not None
#             Alerta.no_mae != None,  # Ensure the mother's name is not None
#         ),
#         and_(
#             Alerta.no_qualificado == Nist.no_pessoa,
#             Alerta.dt_nascimento == Nist.dt_nascimento,
#             Alerta.no_mae == Nist.no_pai,  # Compara nome da mae do alerta com o nome do pai do nist
#             Alerta.no_qualificado != None,  # Ensure the name is not None
#             Alerta.dt_nascimento != None,  # Ensure the DOB is not None
#             Alerta.no_mae != None,  # Ensure the mother's name is not None

#         )
#     )).filter(Nist.ativo==True).add_columns(Nist).all()

#     # Returning a list of tuples, each containing a Nist object and the corresponding Alerta object
#     novos_alertas = [(result[0], result[1]) for result in results if not alerta_ja_existe(result[0].id_alerta, result[1].id_nist) and result[1].base_origem.ativo]        
#     if novos_alertas:        
#         print(f'[stimar] {len(novos_alertas)} novos alertas (matches) descobertos.')
#         return novos_alertas
#     else:
#         print(f'[stimar] Nenhum novo alerta (match) descoberto.')
#         return None


def obtem_novos_alertas() -> tuple:
    """
    Função compara os dados pessoais (nome + data de nascimento + nome da mãe|pai) ou cpf na tabela
    tb_alerta e tb_nist em busca de pessoas com alerta ou restrição (match). Caso encontre,
    retorna uma tupla contendo os IDs dos objetos Alerta e Nist.

    Parâmetros:
    - Nenhum

    Retorno:
    - Tupla contendo os IDs de Alerta e Nist ou None.
    """
    # Realiza a consulta com as condições especificadas
    results = Alerta.query.join(Nist, or_(
        and_(
            Alerta.nr_cpf == Nist.nr_cpf,
            Alerta.nr_cpf != None,  # Assegura que CPF não é None
            Nist.nr_cpf != None,  # Assegura que CPF não é None
        ),
        and_(
            Alerta.no_qualificado == Nist.no_pessoa,
            Alerta.dt_nascimento == Nist.dt_nascimento,
            Alerta.no_mae == Nist.no_mae,
            Alerta.no_qualificado != None,  # Assegura que o nome não é None
            Alerta.dt_nascimento != None,  # Assegura que a data de nascimento não é None
            Alerta.no_mae != None,  # Assegura que o nome da mãe não é None
        ),
        and_(
            Alerta.no_qualificado == Nist.no_pessoa,
            Alerta.dt_nascimento == Nist.dt_nascimento,
            Alerta.no_mae == Nist.no_pai,  # Compara nome da mãe do alerta com o nome do pai do nist
            Alerta.no_qualificado != None,  # Assegura que o nome não é None
            Alerta.dt_nascimento != None,  # Assegura que a data de nascimento não é None
            Alerta.no_mae != None,  # Assegura que o nome da mãe não é None
        )
    )).filter(Nist.ativo == True).add_columns(Nist).all()

    # Itera sobre os resultados e utiliza yield para retornar os pares de IDs
    for result in results:
        alerta, nist = result[0], result[1]
        
        # Verifica se o alerta já existe, se não, retorna o par de IDs
        if not alerta_ja_existe(alerta.id_alerta, nist.id_nist) and nist.base_origem.ativo:
            print(f'[stimar] Novo alerta (match) encontrado: {alerta.id_alerta}, {nist.id_nist}')
            yield (alerta.id_alerta, nist.id_nist)

    # Caso não haja novos alertas, a função retorna None
    print('[stimar] Busca concluída.')
    return None


def obtem_lista_paginada_com_novos_alertas(limit: int = None, offset: int = None) -> List[Tuple[int, int]]:
    """
    Função compara os dados pessoais (nome + data de nascimento + nome da mãe|pai) ou CPF na tabela
    tb_alerta e tb_nist em busca de pessoas com alerta ou restrição (match). Caso encontre,
    retorna uma lista contendo tuplas com os IDs dos objetos Alerta e Nist.

    Parâmetros:
    - limit (int, opcional): Número máximo de resultados a serem retornados.
    - offset (int, opcional): Número de resultados a serem ignorados antes de começar a retornar.

    Retorno:
    - Lista contendo tuplas com os IDs de Alerta e Nist.
    """
    # Verificação de tipos dos parâmetros
    if limit is not None and not isinstance(limit, int):
        raise TypeError("O parâmetro 'limit' deve ser do tipo int ou None.")
    if offset is not None and not isinstance(offset, int):
        raise TypeError("O parâmetro 'offset' deve ser do tipo int ou None.")

    # Configurando a consulta ao banco de dados
    query = Alerta.query.join(Nist, or_(
        and_(
            Alerta.nr_cpf == Nist.nr_cpf,
            Alerta.nr_cpf != None,  # Assegura que CPF não é None
            Nist.nr_cpf != None,  # Assegura que CPF não é None
        ),
        and_(
            Alerta.no_qualificado == Nist.no_pessoa,
            Alerta.dt_nascimento == Nist.dt_nascimento,
            Alerta.no_mae == Nist.no_mae,
            Alerta.no_qualificado != None,  # Assegura que o nome não é None
            Alerta.dt_nascimento != None,  # Assegura que a data de nascimento não é None
            Alerta.no_mae != None,  # Assegura que o nome da mãe não é None
        ),
        and_(
            Alerta.no_qualificado == Nist.no_pessoa,
            Alerta.dt_nascimento == Nist.dt_nascimento,
            Alerta.no_mae == Nist.no_pai,  # Compara nome da mãe do alerta com o nome do pai do nist
            Alerta.no_qualificado != None,  # Assegura que o nome não é None
            Alerta.dt_nascimento != None,  # Assegura que a data de nascimento não é None
            Alerta.no_mae != None,  # Assegura que o nome da mãe não é None
        )
    )).filter(Nist.ativo == True).add_columns(Nist)

    # Aplica os parâmetros de limite e deslocamento se forem fornecidos
    if offset is not None and limit is not None:
        query = query.offset(offset)
        query = query.limit(limit)

    # Obtém os resultados da consulta
    results = query.all()

    # Processa os resultados para retornar apenas os IDs
    novos_alertas = [
        (result[0].id_alerta, result[1].id_nist)
        for result in results
        if not alerta_ja_existe(result[0].id_alerta, result[1].id_nist) and result[1].base_origem.ativo
    ]

    # Loga a quantidade de novos alertas encontrados
    if novos_alertas:
        print(f'[stimar] {len(novos_alertas)} novos alertas (matches) descobertos.')
    else:
        print('[stimar] Nenhum novo alerta (match) descoberto.')

    return novos_alertas


def add_alerta_nist(id_alerta:int, id_nist:int)-> AlertaNist|None:

    if not isinstance(id_nist, int):
        raise TypeError(f'Tipo inválido para "id_nist". Esperado tipo <int>.')
    if not isinstance(id_alerta, int):
        raise TypeError(f'Tipo inválido para "id_alerta". Esperado tipo <int>.')
    
    alerta_nist_existente = AlertaNist.query.filter_by(id_nist=id_nist, id_alerta=id_alerta).first()

    if not alerta_nist_existente:
        novo_alerta_nist = AlertaNist(id_nist=id_nist, id_alerta=id_alerta)
        db.session.add(novo_alerta_nist)
        db.session.flush()
        msg_sucesso = f'AlertaNist #{novo_alerta_nist.id_alerta_nist} adicionado no banco.'
        add_log(cd_tipo_log=40, id_origem=novo_alerta_nist.id_alerta_nist, ds_log=msg_sucesso)

        return novo_alerta_nist
    else:
        pass
        # print(f"[debug] AlertaNist não encontrado. id nist: {id_nist}, id alerta: {id_alerta}.")


def alerta_nist_findface_ja_existe(id_alerta_nist:int, id_findface:int) -> bool:
    if not isinstance(id_alerta_nist, int):
        raise TypeError(f'Tipo inválido para "id_alerta_nist". Esperado tipo <int>.')
    if not isinstance(id_findface, int):
        raise TypeError(f'Tipo inválido para "id_findface". Esperado tipo <int>.')
    
    alerta_nist_findface = AlertaNistFindface.query.filter(AlertaNistFindface.id_alerta_nist==id_alerta_nist, AlertaNistFindface.id_findface==id_findface).first()
    if alerta_nist_findface:
        return True
    else:
        return False
    

def add_alerta_nist_findface(alerta_nist:AlertaNist) -> list:
                
    if not isinstance(alerta_nist, AlertaNist):
        raise TypeError(f'Tipo inválido para "alerta_nist". Esperado tipo <AlertaNist>.')
    
    # Para cada Findface associado ao NIST do alerta_nist
    lista_novos_alerta_nist_findface = []

    todos_findfaces = Findface.query.all()
    for findface in todos_findfaces:
        novo_alerta_nist_findface = AlertaNistFindface(id_alerta_nist=alerta_nist.id_alerta_nist, id_findface=findface.id_findface)
        db.session.add(novo_alerta_nist_findface)
        db.session.commit()
        msg_sucesso = f'Nova relação AlertaNistFindface criada. ID #{novo_alerta_nist_findface.id_alerta_nist_findface}.'
        add_log(cd_tipo_log=50, id_origem=novo_alerta_nist_findface.id_alerta_nist_findface,ds_log=msg_sucesso)
        lista_novos_alerta_nist_findface.append(novo_alerta_nist_findface)
    
    return lista_novos_alerta_nist_findface


def salva_alerta_findface(novos_alertas:tuple) -> None:
    if not isinstance(novos_alertas, list):
        raise TypeError(f'Tipo inválido para "novos_alertas". Esperado tipo "list".')
    
    lista_nist_alerta = []
    for nist, alerta in novos_alertas:
        alerta_nist = AlertaNist(id_nist=nist.id_nist, id_alerta=alerta.id_alerta)
        db.session.add(alerta_nist)
        db.session.commit()
        msg_sucesso = f'Alerta #{alerta_nist.id_alerta_nist} cadastrado no banco para o NIST #{alerta_nist.id_nist} com a restrição #{alerta_nist.id_alerta}'
        add_log(cd_tipo_log=40, id_origem=alerta_nist.id_alerta_nist, ds_log=msg_sucesso)


def inativa_alerta(alerta_nist):

    if not alerta_nist:
        print(f'alerta_nist vazio')
        return None

    # Recupera o alerta para obter o sq_alerta_restricao
    alerta = Alerta.query.filter(Alerta.id_alerta==alerta_nist.id_alerta).first()
    if alerta:
        # Encontra os alertas com com o mesmo sq_alerta_restricao e card_id not null
        result = AlertaNist.query.join(Alerta, AlertaNist.id_alerta == Alerta.id_alerta)\
                                        .filter(Alerta.sq_alerta_restricao == alerta.sq_alerta_restricao,
                                                AlertaNist.card_id.isnot(None))\
                                        .first()

        if result:
            # Encontrou alerta ativo para o alerta a ser inativado no Findface
            print(f'Encontrou o alerta ativo para inativação Alerta #{result.id_alerta} Nist {result.id_nist}.')

            # Encontra o Nist correspondente para chegar recuperar os Findfaces associados
            nist = Nist.query.filter(Nist.id_nist==result.id_nist).first()

            if nist:
                # Encontra os Findfaces associados à base de origem do Nist
                findfaces = nist.base_origem.findfaces

                for findface in findfaces:
                    with FindfaceConnection(findface.url_base, username=FINDFACE_USER, password=FINDFACE_PASSWORD) as ffcon:
                        ff_multi = FindfaceMulti(ffcon)
                        mitra_toolkit = MitraToolkit(ff_multi)

                        card = mitra_toolkit.inativa_card(result.card_id)
                        if card:
                            print(f'[stimar] Card #{card["id"]} inativado no Findface {findface.no_findface}.')
                            alerta_nist.card_id = card["id"]
                            db.session.commit()    
                            print(f'[stimar] Alerta #{alerta_nist.id_alerta} Nist #{alerta_nist.id_nist} atualizado com Card #{card["id"]}.')
            else:
                print(f'[stimar] Nist não encontrado para o ID {alerta_nist.id_nist} ')
        else:
            print(f'[stimar] Nenhum alerta_nist encontrado para apesquisa realizada.')


def envia_alertanistfindface_para_findface(id_alerta_nist_findface: int) -> None:
    if not isinstance(id_alerta_nist_findface, int):
        raise TypeError(f'Tipo <{type(id_alerta_nist_findface)}> inválido para "id_alerta_nist_findface". Esperado <Type int>')

    with app.app_context() as context:

        # Recupera e instancia o objeto AlertaNistFindface
        alerta_nist_findface = AlertaNistFindface.query.filter(AlertaNistFindface.id_alerta_nist_findface==id_alerta_nist_findface).first()
        if not alerta_nist_findface:
            return None

        # Se já houver card cadastrado na relação AlertaNistFindface, retorna None
        if alerta_nist_findface.card_id:
            print(f"[stimar] Card_id já cadastrado para AlertaNistFindface #{id_alerta_nist_findface}.")
            return None
     
        # Recupera, na ordem, AlertaNist, Alerta e Nist relacionados ao AlertaNistFindface
        alertanist = AlertaNist.query.filter(AlertaNist.id_alerta_nist==alerta_nist_findface.id_alerta_nist).first()
        alerta = Alerta.query.filter(Alerta.id_alerta==alertanist.id_alerta).first()
        nist = Nist.query.filter(Nist.id_nist==alertanist.id_nist).first()

        # Instancia um objeto PessoaFindface para enviar ao Findface
        pessoa_ff = PessoaFindface(findface=None, nist=nist.uri_nist)

        # Atualiza a lista de PessoaFindface para a base de alerta correspondente
        if alerta.sq_tipo_alerta_restricao in (4, 7, 9, 13):  # 4, 7, 9 e 13 são Mandados de Prisão
            nome_base_alerta = 'PF/BNMP'
        else:
            db.session.rollback()
            msg_erro = f'sq_tipo_alerta_restricao inválido no Alerta #{alerta.id_alerta}'
            add_log(cd_tipo_log=69, id_origem=alerta.id_alerta, ds_log=msg_erro)
            db.session.commit()
            print('[stimar] ' + msg_erro)
            raise MitraException(msg_erro)

        pessoa_ff.lista = nome_base_alerta

        # Atualiza o status do NIST para o mesmo status da base de origem
        pessoa_ff.ativo = nist.base_origem.ativo

        # Seta o número do mandado de prisão, se houver
        if alerta.nr_mandado_prisao:
            pessoa_ff.bnmp = alerta.nr_mandado_prisao

        # Seta demais atributos necessários para envio ao Findface
        pessoa_ff.findfaces = nist.base_origem.findfaces
        pessoa_ff.uri_nist = nist.uri_nist
        pessoa_ff.id_nist = nist.id_nist

        # Seta o Findface de trabalho
        findface = alerta_nist_findface.findface

        # Obtem o nome do usuário e senha do findface da variável de ambiente
        var_ambiente_usuario_findface = f"{findface.no_findface}_usuario"
        var_ambiente_senha_findface = f"{findface.no_findface}_senha"

        FINDFACE_USER = os.environ[var_ambiente_usuario_findface]
        FINDFACE_PASSWORD = os.environ[var_ambiente_senha_findface]

        # Envia pessoa para o Findface
        with FindfaceConnection(base_url=findface.url_base, username=FINDFACE_USER, password=FINDFACE_PASSWORD) as ffcon:
            ffmulti = FindfaceMulti(ffcon)
            mitra_toolkit = MitraToolkit(ffmulti)
            pessoa_ff.findface = ffmulti

            # Envia o alerta para o(s) Findface(s)
            try:
                cards = mitra_toolkit.add_pessoa_to_findface(pessoa_ff)
                pass
            except Exception as e:
                db.session.rollback()
                msg_erro = f'Erro ao tentar enviar o AlertaNistFindface #{alerta_nist_findface.id_alerta_nist_findface} para o Findface {findface.no_findface} \n' + str(e)
                add_log(cd_tipo_log=69, id_origem=alerta_nist_findface.id_alerta_nist_findface, ds_log=msg_erro)
                alerta_nist_findface.card_id = -1
                db.session.commit()
                print('[stimar] ' + msg_erro)
                raise MitraException(traceback.format_exc())

            if cards:
                if isinstance(cards, dict):
                    card_id = cards["id"]
                    tipo_operacao = "criado"
                if isinstance(cards, (list, tuple)):
                    card_id = cards[0]["id"]
                    tipo_operacao = "atualizado"

                if alerta.tp_status in (1, 4): # Se for criação de alerta
                    # Atualiza o AlertaNistFindface com o card_id
                    alerta_nist_findface.card_id = card_id
                    db.session.flush()
                    msg_sucesso = f'AlertaNistFindface #{alerta_nist_findface.id_alerta_nist_findface} {tipo_operacao} no Findface #{findface.no_findface}, card #{alerta_nist_findface.card_id}.'
                    add_log(cd_tipo_log=60, id_origem=alerta_nist_findface.id_alerta_nist_findface, ds_log=msg_sucesso)
                    print('[stimar] ' + msg_sucesso)
                    
                else:
                    # Se for inativação de alerta (tp_status not int [1, 4])
                    try:
                        card_inativado = mitra_toolkit.inativa_card(card_id)
                    except Exception as e:
                        db.session.rollback()
                        msg_erro = f'Erro ao tentar enviar inativar o AlertaNistFindface #{alerta_nist_findface.id_alerta_nist_findface} no Findface {findface.no_findface} \n' + str(e)
                        add_log(cd_tipo_log=69, id_origem=alerta_nist_findface.id_alerta_nist_findface, ds_log=msg_erro)
                        db.session.commit()
                        print('[stimar] ' + msg_erro)
                        raise MitraException(traceback.format_exc())

                    if card_inativado:
                        card_id = card_inativado["id"]
                        # Atualiza o AlertaNistFindface com o card_id
                        alerta_nist_findface.card_id = card_id
                        db.session.flush()
                        msg_sucesso = f'AlertaNistFindface #{alerta_nist_findface.id_alerta_nist_findface} inativado no Findface #{findface.no_findface}, card #{alerta_nist_findface.card_id}.'
                        add_log(cd_tipo_log=61, id_origem=alerta_nist_findface.id_alerta_nist_findface, ds_log=msg_sucesso)
                        print('[stimar] ' + msg_sucesso)
                    else:
                        db.session.rollback()
                        raise MitraException(f'"mitra_toolkit.inativa_card() retornou None. Esperado card." ')

                db.session.commit()
                # return (alerta_nist_findface.id_alerta_nist_findface, card_id)
            else:
                db.session.rollback()
                msg_erro = f"Tipo inválido para 'cards'."                
                add_log(cd_tipo_log=69, id_origem=alerta_nist_findface.id_alerta_nist_findface, ds_log=msg_erro)
                db.session.commit()
                print('[stimar] ' + msg_erro)
                raise MitraException(msg_erro)


def obter_findfaces_com_alertanistfindface():

    lista_findfaces = []

    for findface in Findface.query.all():
        alerta_with_associations = []

        # Fetch all Alerta entries
        all_alerta = Alerta.query.all()

        for alerta in all_alerta:
            # Initialize the list to hold corresponding AlertaNistFindface items
            all_alertanistfindface = []

            # Fetch corresponding AlertaNist entries for the current Alerta
            alertanists = AlertaNist.query.filter_by(id_alerta=alerta.id_alerta).all()

            # For each AlertaNist, fetch corresponding AlertaNistFindface entries
            for alertanist in alertanists:
                alertanistfindfaces = AlertaNistFindface.query.filter_by(id_alerta_nist=alertanist.id_alerta_nist, card_id=None).all()
                # alertanistfindfaces = AlertaNistFindface.query.filter(AlertaNistFindface.id_alerta_nist==alertanist.id_alerta_nist, AlertaNistFindface.card_id==None).all()
                if alertanistfindfaces:
                    all_alertanistfindface.extend(alertanistfindfaces)

            # Append the tuple (Alerta, List of AlertaNistFindface) to the result list
            # alerta_with_associations.append((alerta, all_alertanistfindface))

            if all_alertanistfindface:
                lista_findfaces.append(all_alertanistfindface)
            # lista_findfaces.append((findface, alerta, all_alertanistfindface))

    return lista_findfaces


def envio_paralelo_alertanistfindface(id_alerta_nist_findface) -> None:

    try:
        envia_alertanistfindface_para_findface(id_alerta_nist_findface)
    except Exception as e:
        with app.app_context() as context:
            print(f"[stimar] Erro ao processar o AlertaNistFindface #{id_alerta_nist_findface}.")
            add_log(cd_tipo_log=69, id_origem=id_alerta_nist_findface, ds_log=str(e))
            db.session.commit()
            print(traceback.format_exc())


def update_paralelo_alertanistfidface_with_card_id(lista_alertanistfindface_cardid):
    with app.app_context() as context:
        for id_alerta_nist_findface, new_card_id in lista_alertanistfindface_cardid:
            alerta_nist_findface = AlertaNistFindface.query.filter_by(id_alerta_nist_findface=id_alerta_nist_findface).first()
            alerta_nist_findface.card_id = new_card_id
            db.session.commit()
            print(f'[stimar] AlertaNistFindface #{alerta_nist_findface.id_alerta_nist_findface} atualizado com o card #{alerta_nist_findface.card_id}')


# def add_alerta_nist_em_paralelo(tupla_alerta_nist):
#     with app.app_context() as context:
#         id_alerta = tupla_alerta_nist[0].id_alerta
#         id_nist = tupla_alerta_nist[1].id_nist
#         # novo_alerta_nist = add_alerta_nist(tupla_alerta_nist[0], tupla_alerta_nist[1])
#         novo_alerta_nist = add_alerta_nist(id_alerta, id_nist)
#         if novo_alerta_nist:
#             add_alerta_nist_findface(novo_alerta_nist)
#         else:
#             print("Nenhum AlertaNist retornado.")


def add_alerta_nist_em_paralelo(alerta_id, nist_id):
    with app.app_context() as context:
        novo_alerta_nist = add_alerta_nist(alerta_id, nist_id)
        if novo_alerta_nist:
            add_alerta_nist_findface(novo_alerta_nist)
        else:
            print("Nenhum AlertaNist retornado.")


# def add_all_alerta_nist(lista_tuplas_alerta_nist: List[Tuple[object, object]]) -> None:
#     """
#     Adiciona uma lista de relações Alerta-NIST ao banco de dados.
    
#     Parameters:
#         lista_tuplas_alerta_nist (List[Tuple[object, object]]): Lista de tuplas contendo objetos de Alerta e NIST.
        
#     Raises:
#         TypeError: Se o parâmetro não for do tipo esperado ou se os objetos dentro das tuplas não contiverem os atributos esperados.
#     """
#     # Verificar se o parâmetro é uma lista
#     if not isinstance(lista_tuplas_alerta_nist, list):
#         raise TypeError("O parâmetro lista_tuplas_alerta_nist deve ser uma lista de tuplas.")
    
#     # Verificar se todos os elementos da lista são tuplas
#     for tupla in lista_tuplas_alerta_nist:
#         if not isinstance(tupla, tuple) or len(tupla) != 2:
#             raise TypeError("Cada elemento da lista deve ser uma tupla com dois objetos.")
#         alerta, nist = tupla
#         if not hasattr(alerta, 'id_alerta') or not hasattr(nist, 'id_nist'):
#             raise TypeError("Os objetos nas tuplas devem conter os atributos 'id_alerta' e 'id_nist'.")
    
#     # Criar objetos AlertaNist
#     with app.app_context():  # Certifique-se de que `app` está configurado corretamente
#         try:
#             todos_alerta_nists = [
#                 AlertaNist(id_alerta=alerta.id_alerta, id_nist=nist.id_nist) for alerta, nist in lista_tuplas_alerta_nist
#             ]
#             db.session.add_all(todos_alerta_nists)
#             db.session.commit()
#         except Exception as e:
#             db.session.rollback()  # Reverter transação em caso de erro
#             raise e


def add_all_alerta_nist(lista_tuplas_ids: List[Tuple[int, int]]) -> None:
    """
    Adiciona uma lista de relações Alerta-NIST ao banco de dados.
    
    Parameters:
        lista_tuplas_ids (List[Tuple[int, int]]): Lista de tuplas contendo IDs de Alerta e NIST.
        
    Raises:
        TypeError: Se o parâmetro não for do tipo esperado ou se os elementos das tuplas não forem inteiros.
    """
    # Verificar se o parâmetro é uma lista
    if not isinstance(lista_tuplas_ids, list):
        raise TypeError("O parâmetro lista_tuplas_ids deve ser uma lista de tuplas contendo IDs.")
    
    # Verificar se todos os elementos da lista são tuplas de dois inteiros
    for tupla in lista_tuplas_ids:
        if not isinstance(tupla, tuple) or len(tupla) != 2:
            raise TypeError("Cada elemento da lista deve ser uma tupla contendo dois IDs (int).")
        id_alerta, id_nist = tupla
        if not isinstance(id_alerta, int) or not isinstance(id_nist, int):
            raise TypeError("Os elementos das tuplas devem ser inteiros representando IDs.")
    
    # Criar objetos AlertaNist
    with app.app_context():  # Certifique-se de que `app` está configurado corretamente
        try:
            todos_alerta_nists = [
                AlertaNist(id_alerta=id_alerta, id_nist=id_nist) for id_alerta, id_nist in lista_tuplas_ids
            ]
            db.session.add_all(todos_alerta_nists)
            db.session.commit()
            print(f"[stimar] {len(todos_alerta_nists)} relações Alerta-NIST adicionadas com sucesso.")
        except Exception as e:
            db.session.rollback()  # Reverter transação em caso de erro
            print(f"[stimar] Erro ao adicionar relações Alerta-NIST: {e}")
            raise e


def descobre_novos_alertas_bnmp_subquery():
    """
    Verifica coincidências entre tb_nist e tb_alerta utilizando subqueries para otimizar performance,
    garantindo que não haja duplicação e que o Nist possua base de origem ativa.
    """
    print(f"[stimar] Descobrindo novos alertas do BNMP (matches)...")
    try:
        subquery_nist = db.session.query(Nist.id_nist, Nist.nr_cpf, Nist.no_pessoa, Nist.dt_nascimento, Nist.no_mae, Nist.no_pai, Nist.id_base_origem).subquery()
        subquery_alerta = db.session.query(Alerta.id_alerta, Alerta.nr_cpf, Alerta.no_qualificado, Alerta.dt_nascimento, Alerta.no_mae).subquery()
        
        matches_query = (
            db.session.query(subquery_nist.c.id_nist, subquery_alerta.c.id_alerta)
            .filter(
                (subquery_alerta.c.nr_cpf == subquery_nist.c.nr_cpf) &
                (subquery_alerta.c.nr_cpf.isnot(None)) &
                (subquery_nist.c.nr_cpf.isnot(None))
            )
            .union(
                db.session.query(subquery_nist.c.id_nist, subquery_alerta.c.id_alerta)
                .filter(
                    (subquery_alerta.c.no_qualificado == subquery_nist.c.no_pessoa) &
                    (subquery_alerta.c.dt_nascimento == subquery_nist.c.dt_nascimento) &
                    (subquery_alerta.c.no_mae == subquery_nist.c.no_mae) &
                    (subquery_alerta.c.no_qualificado.isnot(None)) &
                    (subquery_alerta.c.dt_nascimento.isnot(None)) &
                    (subquery_alerta.c.no_mae.isnot(None)) &
                    (subquery_nist.c.no_mae.isnot(None))
                )
            )
            .union(
                db.session.query(subquery_nist.c.id_nist, subquery_alerta.c.id_alerta)
                .filter(
                    (subquery_alerta.c.no_qualificado == subquery_nist.c.no_pessoa) &
                    (subquery_alerta.c.dt_nascimento == subquery_nist.c.dt_nascimento) &
                    (subquery_alerta.c.no_mae == subquery_nist.c.no_pai) &
                    (subquery_alerta.c.no_qualificado.isnot(None)) &
                    (subquery_alerta.c.dt_nascimento.isnot(None)) &
                    (subquery_alerta.c.no_mae.isnot(None)) &
                    (subquery_nist.c.no_pai.isnot(None))
                )
            )
        )
        
        # lista_novos_alerta_nist = []
        # for id_nist, id_alerta in matches_query.all():
        #     if not db.session.query(AlertaNist).filter_by(id_nist=id_nist, id_alerta=id_alerta).first():
        #         if db.session.query(BaseOrigem).filter_by(id_base_origem=id_nist).filter(BaseOrigem.ativo == True).first():
        #             lista_novos_alerta_nist.append(AlertaNist(id_nist=id_nist, id_alerta=id_alerta))

        lista_novos_alerta_nist = []
        for id_nist, id_alerta in matches_query.all():
            if not db.session.query(AlertaNist).filter_by(id_nist=id_nist, id_alerta=id_alerta).first():
                nist_atual_base_origem = db.session.query(Nist).filter_by(id_nist=id_nist).first().id_base_origem
                if db.session.query(BaseOrigem).filter_by(id_base_origem=nist_atual_base_origem).filter(BaseOrigem.ativo == True).first():
                    lista_novos_alerta_nist.append(AlertaNist(id_nist=id_nist, id_alerta=id_alerta))


        print(f"[stimar] {len(lista_novos_alerta_nist)} alerta(s) (matches) encontrado(s). Salvado...")
        if lista_novos_alerta_nist:
            db.session.add_all(lista_novos_alerta_nist)
            db.session.commit()
            print("[stimar] Novos alertas NIST vinculados com sucesso.")
        else:
            print("[stimar] Nenhum novo alerta vinculado.")
    
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro ao inserir registros: {str(e)}")
    except Exception as e:
        db.session.rollback()
        print(f"Erro inesperado: {str(e)}")


def descobre_novos_alertas_bnmp_join():
    """
    Verifica coincidências entre tb_nist e tb_alerta utilizando JOIN direto para otimizar performance,
    garantindo que não haja duplicação e que o Nist possua base de origem ativa.
    """

    print(f"[stimar] Descobrindo novos alertas do BNMP (matches)...")
    try:
        matches_query = (
            db.session.query(Alerta.id_alerta, Nist.id_nist)
            .join(Nist, or_(
                and_(Alerta.nr_cpf == Nist.nr_cpf, Alerta.nr_cpf.isnot(None), Nist.nr_cpf.isnot(None)),
                and_(Alerta.no_qualificado == Nist.no_pessoa, Alerta.dt_nascimento == Nist.dt_nascimento, 
                        Alerta.no_mae == Nist.no_mae, Alerta.no_qualificado.isnot(None), Alerta.dt_nascimento.isnot(None), Alerta.no_mae.isnot(None), Nist.no_mae.isnot(None)),
                and_(Alerta.no_qualificado == Nist.no_pessoa, Alerta.dt_nascimento == Nist.dt_nascimento, 
                        Alerta.no_mae == Nist.no_pai, Alerta.no_qualificado.isnot(None), Alerta.dt_nascimento.isnot(None), Alerta.no_mae.isnot(None), Nist.no_pai.isnot(None))
            ))
            .filter(Nist.ativo == True, Nist.base_origem.has(ativo=True))
        )
        
        lista_novos_alerta_nist = []
        for id_alerta, id_nist in matches_query.all():
            existe = db.session.query(AlertaNist).filter_by(id_nist=id_nist, id_alerta=id_alerta).first()
            if not existe:
                lista_novos_alerta_nist.append(AlertaNist(id_nist=id_nist, id_alerta=id_alerta))

        print(f"[stimar] {len(lista_novos_alerta_nist)} alerta(s) (matches) encontrado(s). Salvado...")
        if lista_novos_alerta_nist:
            db.session.add_all(lista_novos_alerta_nist)
            db.session.commit()
            print("[stimar] Novos alertas NIST vinculados com sucesso usando JOIN.")
        else:
            print("[stimar] Nenhum novo alerta vinculado.")
    
    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro ao inserir registros: {str(e)}")
    except Exception as e:
        db.session.rollback()
        print(f"Erro inesperado: {str(e)}")


def vincula_alertanist_com_findface():
    """
    Cria uma entrada na tabela tb_alerta_nist_findface para cada combinação
    existente entre tb_alerta_nist e tb_findface, otimizando a inserção com db.session.add_all().
    """
    try:
        # Alias para as tabelas
        alerta_nist = aliased(AlertaNist)
        alerta_nist_findface = aliased(AlertaNistFindface)

        # Consulta para encontrar IDs de AlertaNist sem correspondência em AlertaNistFindface
        query = (
            db.session.query(alerta_nist.id_alerta_nist)
            .outerjoin(alerta_nist_findface, alerta_nist.id_alerta_nist == alerta_nist_findface.id_alerta_nist)
            .filter(alerta_nist_findface.id_alerta_nist_findface == None)
        )
        ids_alerta_nist_sem_findface = [row[0] for row in query.all()]

        # Consulta para obter todos os IDs da tabela Findface
        query = db.session.query(Findface.id_findface)
        ids_findface = [row[0] for row in query.all()]

        lista_novos_alerta_nist_findface = [
            AlertaNistFindface(id_alerta_nist=alerta_nist_id, id_findface=findface_id)
            for findface_id in ids_findface
            for alerta_nist_id in ids_alerta_nist_sem_findface
        ]
        
        print(f"[stimar] Adicionando {len(lista_novos_alerta_nist_findface)} registros em AlertaNistFindface...")
        
        if lista_novos_alerta_nist_findface:
            db.session.add_all(lista_novos_alerta_nist_findface)
            db.session.commit()
            print("[stimar] Vinculações AlertaNistFindface criadas com sucesso.")
        else:
            print("[stimar] Nenhum novo vínculo necessário.")

    except IntegrityError as e:
        db.session.rollback()
        print(f"Erro ao inserir registros: {str(e)}")
    except Exception as e:
        db.session.rollback()
        print(f"Erro inesperado: {str(e)}")


if __name__ == '__main__':

    with app.app_context() as context:
        dt_ultma_atualizacao_stimar = obtem_dt_ultima_atualizacao_stimar()
        print(f'[stimar] Ultima atualização STIMAR:  {dt_ultma_atualizacao_stimar.strftime(r"%Y-%m-%d %H:%M:%S.%f")}')

        #============================================================#
        # Baixa novas restrições do STIMAR
        #============================================================#
        try:
            download_alertas_stimar(dt_ultma_atualizacao_stimar)    
        except Exception as e:
            print(traceback.format_exc())
        
        #============================================================#
        # Descobre se há novos alertas (matches)        
        #============================================================#
        dt1 = datetime.now()
        descobre_novos_alertas_bnmp_subquery()
        # descobre_novos_alertas_bnmp_join()
        dt2 = datetime.now()
        diferenca = calcular_diferenca_tempo(dt1, dt2)
        print(f"Tempo transcorrido: {diferenca['horas']}h {diferenca['minutos']}m {diferenca['segundos']}s ")

        #====================================================================================#
        # Cria as vinculações entre AlertaNist e Findface
        #====================================================================================#
        vincula_alertanist_com_findface()

        #====================================================================================#
        # Pesquisa os alertas (AlertaNistFindface) que não foram enviados aos Findfaces
        #====================================================================================#
        lista_ids_alertanistfindface_sem_cardid = [x.id_alerta_nist_findface for x in AlertaNistFindface.query.filter(AlertaNistFindface.card_id == None).all()]
        print(f"[stimar] {len(lista_ids_alertanistfindface_sem_cardid)} alertas para enviar ao Findface.")

        #====================================================================================#
        # Envia para os AlertaNistFindface sem card_id para o respectivo Findface
        #====================================================================================#
        if lista_ids_alertanistfindface_sem_cardid:
            print(f"[stimar] Enviando...")
            MAX_WORKERS = int(os.cpu_count() * 0.8)
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                result = executor.map(envio_paralelo_alertanistfindface, lista_ids_alertanistfindface_sem_cardid)

        else:
            print(f'[stimar] Nenhum alerta pendente de envio ao Findface.')

        print('[stimar] Script finalizado.')