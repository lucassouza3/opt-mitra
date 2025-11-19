import telebot
import app
from local.utils import verifica_username
from datetime import datetime
# import locale
import hashlib
import os
from base64 import b64decode
from pathlib import Path
import requests
from local.logger import logger
from telebot import apihelper
import traceback
from findface_multi.findface_multi import *
from functions import validar_celular_brasileiro, validate_cpf, remove_non_alphanumeric
import io


# Configurações
# findface_url = 'https://sdf0889.pf.gov.br'
# BotRR
# bot_token = '6349717720:AAH4X1PoibbN3aEO4YgFqRKVd7ysd2940rU'

findface_url = os.environ["TELEGRAM_BOT_FINDFACE_URL"]
bot_token = os.environ["TELEGRAM_BOT_TOKEN"]

bot = telebot.TeleBot(bot_token)

# Teste
# bot = telebot.TeleBot("5512873129:AAHIRPRCnd4-l2eRlY7QX_PWiVTEJd7nVEU")

def obter_perfil_usuario(username):

    usuario = app.get_user_by_username(username)

    perfil = None
    if usuario:
        if usuario.perfil == 1:
            perfil = 'admin'
        elif usuario.perfil == 2:
            perfil = 'usuario'

    return perfil
    

def usuario_tem_acesso(username):
    
    if obter_perfil_usuario(username) in ['admin', 'usuario']:
        return True
    else:
        return False
    
def usuario_admin(username):

    if obter_perfil_usuario(username) in ['admin']:
        return True
    else:
        return False


def log_message(mensagem):
    texto_log = f'{datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")} {mensagem.from_user.username}: '
    texto_log += f'{mensagem.text} ({mensagem.content_type})'
    app.add_log(username=mensagem.from_user.username, message=texto_log)

    return f'{mensagem.from_user.username}->MitraBot\t{mensagem.text} ({mensagem.content_type})'


def log_resposta(texto, usuario):
    if '\n' in texto:
        texto_log = f'{datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")} MitraBot: \n'
        linhas = texto.split('\n')
        for linha in linhas:
            texto_log += f'\t{linha}\n'
    else:
        texto_log = f'{datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")} MitraBot: {texto}'

    app.add_log(username=usuario, message=texto_log)

    texto_modificado = texto.replace("\n", "; ")
    return f'MitraBot->{usuario}: {texto_modificado}'


@bot.message_handler(commands=['listar_usuarios'])
def admin_listar(message):
    logger.info(log_message(message))
    # Get the sender's username and phone number (if available)
    message_username = message.from_user.username
    message_phone_number = message.contact.phone_number if message.contact else None
    message_chat_id = message.chat.id
    # Get the text sent by the user
    message_text = message.text
    comando = message_text.strip().lower()

    if not usuario_tem_acesso(message_username):
        text_message = 'Usuário não tem permissão para conversar com o bot.'
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)
        return False

    if not usuario_admin(message_username):
        text_message = 'Usuário não tem permissão para este comando.'
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)
        return False
    
    if comando == '/listar_usuarios':
        usuarios = app.get_all_users()
        if len(usuarios) < 0:
            text_message = f'Nenhum usuário cadastrado.'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
        else:
            # Envia uma lista com os usuários. Cada usuário possui um link para o detalhamento
            linhas_mensagem = []
            for idx, usuario in enumerate(usuarios, start=1):
                perfil = ''
                if obter_perfil_usuario(usuario.username) in ['admin']:
                    perfil = '(admin)'                
                linhas_mensagem.append(f'{idx}. {usuario.username} {perfil}')
            text_message = '\n'.join(linhas_mensagem)
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
    

@bot.message_handler(commands=['cadastrar_admin', 'cadastrar_usuario', 'remover_usuario', 'detalhar_usuario', 'log_usuario'])
def admin_usuario(message):
    logger.info(log_message(message))

    # Get the sender's username and phone number (if available)
    message_username = message.from_user.username
    message_phone_number = message.contact.phone_number if message.contact else None
    message_chat_id = message.chat.id
    # Get the text sent by the user
    message_text = message.text

    if not usuario_tem_acesso(message_username):
        text_message = 'Usuário não tem permissão para conversar com o bot.'
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)
        return False

    if not usuario_admin(message_username):
        text_message = 'Usuário não tem permissão para este comando.'
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)
        return False
    
    parametros = message_text.split()
    comando = parametros[0]

    if comando in ('/remover_usuario', '/detalhar_usuario', '/log_usuario'):
        # Verifica a quantidade de parâmetros informados
        if len(parametros) < 2:
            # Send the message to the specified chat
            text_message = f'Parametros inválidos. Ex.: {comando} <nome>'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
            return None
    elif comando in ('/cadastrar_admin', '/cadastrar_usuario'):

        # Verifica a quantidade de parâmetros informados
        if len(parametros) < 4:
            # Send the message to the specified chat
            text_message = f'Parametros inválidos. '
            text_message += f'\nUso: {comando} <nome_usuario> <cpf> <lotação> <celular> '
            text_message += f'\nEx.: {comando} AndreLuiz 123.456.789-00 SR/PF/RR 95-98123-4567'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
            return None
    else:
        text_message = f'"{comando}" inválido.'
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)

    
    username = parametros[1]

    # Verifica se o nome de usuário é válido
    if comando in ('/remover_usuario', '/log_usuario'): 
        if not verifica_username(username):
            text_message = 'Nome de usuário inválido. Nome do usário deve conter de 5 a 32 caracteres, podendo conter letras números e "_". Caracteres especiais não são permitidos'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
            return False

    if comando in ['/cadastrar_admin', '/cadastrar_usuario']:

        # Verifica se o usuários já está cadastrado
        usuario = app.get_user_by_username(username)
        if usuario is not None:
            bot.send_message(message_chat_id, f'Usuario "{username}" já cadastrado.')
        else:
            perfil = 2
            if comando == '/cadastrar_admin':
                perfil = 1
            cpf = parametros[2]
            if not validate_cpf(cpf):
                # Send the message to the specified chat
                text_message = f'CPF "{cpf}" inválido.'
                logger.info(log_resposta(text_message, message_username))
                bot.send_message(message_chat_id, text_message)
                return None

            lotacao = parametros[3]
            
            celular = parametros[4]
            if not validar_celular_brasileiro(celular):
                # Send the message to the specified chat
                text_message = f'Celular "{celular}" inválido. Ex. 95-98123-4567'
                logger.info(log_resposta(text_message, message_username))
                bot.send_message(message_chat_id, text_message)
                return None

            usuario = app.get_user_by_username(username)
            if usuario is not None:
                text_message = f'Usuario "{username}" já cadastrado.'
                logger.info(log_resposta(text_message, message_username))
                bot.send_message(message_chat_id, text_message)
            else:
                if app.create_usuario(username, perfil, criador=message_username, data_criacao=datetime.now(), cpf=cpf, lotacao=lotacao, celular=celular):
                    text_message = f'Usuário "{username}" cadastrado com sucesso!'
                    logger.info(log_resposta(text_message, message_username))
                    bot.send_message(message_chat_id, text_message)
                else:
                    text_message = f'Erro ao tentar criar usuário "{username}"'
                    logger.info(log_resposta(text_message, message_username))
                    bot.send_message(message_chat_id, text_message)

    
    elif comando == '/remover_usuario':
        usuario = app.get_user_by_username(username)
        if usuario is not None:
            if app.delete_usuario(usuario.id):
                text_message = f'Usuário "{username}" excluído.'
                logger.info(log_resposta(text_message, message_username))
                bot.send_message(message_chat_id, text_message)
            else:
                text_message = f'Erro na exclusão do usuário "{username}".'
                logger.info(log_resposta(text_message, message_username))
                bot.send_message(message_chat_id, text_message)
        else:
            text_message = f'Usuário "{username}" não encontrado.'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)

    elif comando == '/detalhar_usuario':
        # print(f'Entrou no comando "detalhar_usuario". @{username}')
        # usuario = app.get_user_by_username(username)
        usuario = app.get_user_by_username_or_cpf(remove_non_alphanumeric(username))
        if usuario is not None:
            texto_resposta = []
            texto_resposta.append(f'Usuário: {usuario.username}')
            texto_resposta.append(f'Perfil: {obter_perfil_usuario(usuario.username)}')
            texto_resposta.append(f'Criador: {usuario.criador}')
            texto_resposta.append(f'Data de criação: {usuario.data_criacao.strftime(r"%d/%m/%Y")}')
            texto_resposta.append(f'CPF: {usuario.cpf}')
            texto_resposta.append(f'Lotação: {usuario.lotacao}')
            texto_resposta.append(f'Celular: {usuario.celular}')
            text_message = '\n'.join(texto_resposta)
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
        else:
            text_message = f'Usuário "{username}" não encontrado.'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)

    elif comando == '/log_usuario':
        usuario = app.get_user_by_username(username)
        if not usuario:
            text_message = f'Usuário "{username}" não encontrado.'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
            return

        bot.send_message(message_chat_id, f'Lendo log do usuário {username}. Aguarde...')
        
        linhas_log = app.obter_log_usuario(username)
        
        if linhas_log:
            arquivo = io.StringIO()
            for linha in linhas_log:
                texto_linha = f'{linha.ds_log}\n'
                arquivo.write(texto_linha)

            arquivo.seek(0)

            # Define o nome do arquivo usando um dicionário
            files = {'document': (f'Log_{username}.txt', arquivo)}
            
            # Envia o arquivo para o chat
            bot.send_document(message.chat.id, files['document'], caption="Aqui está o seu arquivo!")

  
# Função que realiza o reconhecimento facial
@bot.message_handler(content_types=['photo', 'document'])
def foto_recebida(message):

    try:

        # Get username and chat ID and phone number (if available)
        message_username = message.from_user.username
        message_phone_number = message.contact.phone_number if message.contact else None
        message_chat_id = message.chat.id

        if not usuario_tem_acesso(message_username):
            text_message = 'Usuário não tem permissão para conversar com o bot.'
            logger.info(log_resposta(text_message, message_username))
            bot.send_message(message_chat_id, text_message)
            return False
            
        if message.content_type == 'photo':
            fileID = message.photo[-1].file_id
            file_info = bot.get_file(fileID)
            # file_content = bot.download_file(file_info.file_path)
            
        elif message.content_type == 'document':
            # Se a imagem recebida é um documento do tipo imagem
            if 'image/' in message.document.mime_type:
                fileID = message.document.file_id
                file_info = bot.get_file(fileID)
                # file_content = bot.download_file(file_info.file_path)
            else:
                bot.send_message(message.chat.id, f'Tipo de arquivo inválido. Somente imagens são aceitas.')
                return
        else:
            bot.send_message(message.chat.id, f'Tipo de arquivo inválido. Somente imagens são aceitas.')
            return

        file_content = bot.download_file(file_info.file_path)
        file_hash = hashlib.md5(file_content).hexdigest()
        filename = file_hash + '.jpg'

        # Atualiza o campo texto da mensagem recebida para o nome do arquivo
        # Necessário para registar o nome do arquivo no Log
        message.text = filename
        logger.info(log_message(message))

        # Se o diretório ./Download não existe, cria-o
        download_dir = Path(__file__).parent / 'Download'
        if not download_dir.exists():
            os.mkdir(download_dir)

        # Salva o arquivo no diretorio Download
        filepath = download_dir / filename
        with open(filepath, 'wb') as wbf:
            wbf.write(file_content)

        usuario = os.environ["USUARIO_CONSULTA_FF"]
        senha = os.environ["SENHA_CONSULTA_FF"]

        with FindfaceConnection(base_url=findface_url, username=usuario, password=senha) as findface_conn:

            findface = FindfaceMulti(findface_conn)
            
            detection = findface.detect(file_content, face={})

            cards_humans = []
            for face in detection["objects"]["face"]:

                response = findface.get_human_cards(looks_like=f'detection:{face["id"]}')
                if len(response["results"]) > 0:
                    cards_humans.extend(response["results"])

            if len(cards_humans) > 0:

                for card in cards_humans:

                    card_id = card["id"]

                    data = {"card": [card_id]}
                    face_objects = findface.get_face_objects(card=card_id)["results"]

                    for face_object in face_objects:
                        url_foto = face_object["source_photo"]

                        response = requests.get(url_foto, verify=False)

                        if 200 <= response.status_code < 300:

                            foto_bin = response.content

                            bot.send_photo(message.chat.id, foto_bin)
                            text_message = f'Nome: {card["name"]}\n'

                            try:
                                dt_nascimento = datetime.fromisoformat(card["meta"]["data_nascimento"])
                            except Exception as e:
                                dt_nascimento = None                    
                            if dt_nascimento:
                                text_message += f'Nascimento: {dt_nascimento.strftime("%d/%m/%Y")}\n'
                                
                            if card["meta"]["nacionalidade"]:
                                text_message += f'Nacionalidade: {card["meta"]["nacionalidade"]}\n'
                            if card["meta"]["mae"]:
                                text_message += f'Filiacao 1: {card["meta"]["mae"]}\n'
                            if card["meta"]["pai"]:                    
                                text_message += f'Filiacao 2: {card["meta"]["pai"]}\n'
                            if card["meta"]["cpf"]:
                                text_message += f'CPF: {card["meta"]["cpf"]}\n'
                            if card["meta"]["passaporte"]:
                                text_message += f'Passaporte: {card["meta"]["passaporte"]}\n'
                            if card["meta"]["rnm"]:
                                text_message += f'RNM: {card["meta"]["rnm"]}\n'
                            if card["meta"]["documento"]:
                                text_message += f'Documento: {card["meta"]["documento"]}\n'
                            if card["looks_like_confidence"]:
                                semelhanca = card["looks_like_confidence"] * 100
                                truncado = "{:.2f}".format(semelhanca)
                                text_message += f'Semelhança: {truncado}%\n'
                            if card["watch_lists"]:
                                list_names = [findface.get_watch_list_name_by_id(x) for x in card["watch_lists"]]
                                bases = ', '.join(list_names)
                                text_message += f'Bases: {bases}\n'                        
                            
                            if "PF/BNMP" in list_names and card["active"]:
                                text_message += f'**ALERTA!!! Pessoa com mandado de prisão {card["meta"]["bnmp"]}. Consultar BNMP.**'

                            logger.info(log_resposta(text_message, message_username))
                            bot.send_message(message.chat.id, text_message)

                            recado = "Atenção! O reconhecimento facial é um indicativo e não deve ser utilizado como certeza da identidade da face pesquisada. "
                            recado += "A identificação criminal deve obedecer o disposto na Lei nº 12.037/2009."
                            bot.send_message(message.chat.id, recado)


                        else:
                            print(response.text)

            else:
                text_message = "Nenhum cadastro encontrado."
                bot.send_message(message.chat.id, text_message)
    
    except Exception as e:
        tb = traceback.format_exc()
        text_message = tb
        # logger.info(log_resposta(text_message, message_username))
        bot.send_message(message.chat.id, text_message)


# Função que responde se nenhum comando foi reconhecido
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    logger.info(log_message(message))

    # Get the sender's username and phone number (if available)
    message_username = message.from_user.username
    message_phone_number = message.contact.phone_number if message.contact else None
    message_chat_id = message.chat.id
    # Get the text sent by the user
    message_text = message.text

    if not usuario_tem_acesso(message_username):
        text_message = 'Usuário não tem permissão para conversar com o bot.'
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)
        return False

    if usuario_admin(message_username):
    # Mensagem de boas vindas
        texto_admin = """
/cadastrar_admin
/cadastrar_usuario
/remover_usuario
/listar_usuarios
/detalhar_usuario
/log_usuario
    """
        text_message = texto_admin
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)
    
    else:  # Se for um usuário sem privilegio de administrador
        text_message = "Bem vindo ao chabot! Envie uma foto para reconhecimento."
        logger.info(log_resposta(text_message, message_username))
        bot.send_message(message_chat_id, text_message)


if __name__ == '__main__':
    bot.polling()
