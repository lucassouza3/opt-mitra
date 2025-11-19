from flask import Flask
from sqlalchemy import or_
from database.models import db, Usuario, UsuarioLog
from pathlib import Path
from datetime import datetime, timedelta
from unidecode import unidecode

app = Flask(__name__)
sqlite_database_file = Path(__file__).parent / 'database/database.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{sqlite_database_file}'
# app.config['SQLALCHEMY_ECHO'] = True

db.init_app(app)

with app.app_context():
    db.create_all()

#
# Funções de manipulação dos Usuários
#
def get_all_users():
    with app.app_context():
        users = Usuario.query.order_by(Usuario.perfil, Usuario.username).all()
        return users    


def get_user_by_username(username):
    with app.app_context():
        user = Usuario.query.filter(Usuario.username == username).first()
        return user


def get_user_by_username_or_cpf(parametro):
    with app.app_context():
        # Constrói a consulta usando o operador 'or_' para verificar ambos os campos
        usuario = Usuario.query.filter(
            or_(
                Usuario.username == parametro,
                Usuario.cpf == parametro
            )
        ).first()

        return usuario        


def create_usuario(username, perfil, criador, data_criacao, cpf, lotacao, celular):
    with app.app_context():
        try:
            usuario = Usuario(username=username, perfil=perfil, criador=criador, data_criacao=data_criacao, cpf=cpf, lotacao=lotacao, celular=celular)
            db.session.add(usuario)
            db.session.commit()
            return usuario.id
        except:
            db.session.rollback()
            pass            


def update_usuario(usuario_id, nome, perfil):
    with app.app_context():
        usuario = Usuario.query.filter(Usuario.id == usuario_id).first()
        if usuario:
            usuario.nome = nome
            usuario.perfil = perfil
            db.session.commit()
            return True
        return False


def delete_usuario(usuario_id):
    with app.app_context():
        usuario = Usuario.query.filter(Usuario.id == usuario_id).first()
        if usuario:            
            db.session.delete(usuario)
            db.session.commit()
            print('Usuário removido...')
            return True


def add_log(username, message):
    with app.app_context():
        log = UsuarioLog(username=username, ds_log=message)
        db.session.add(log)
        db.session.commit()
        return True


def obter_log_usuario(username):
    with app.app_context():
        log_usuario = UsuarioLog.query.filter(UsuarioLog.username == username).all()
        return log_usuario
        

with app.app_context():
    # Cadastra os admins    
    admins = [
        {"username": "LeoDantasRR", "perfil": 1, "criador": "sistema", "data_criacao": datetime.now(), "cpf": "62396927272", "lotacao": "SR/PF/RR", "celular": "95981021111"},
        {"username": "Renato_RRC", "perfil": 1, "criador": "sistema", "data_criacao": datetime.now(), "cpf": "04103592621", "lotacao": "SR/PF/RR", "celular": "95981191503"}
        ]
    for admin in admins:
        usuario = get_user_by_username(admin["username"])
        if not usuario:
            if create_usuario(username=admin["username"], perfil=1, criador='sistema', data_criacao=datetime.now(), cpf=admin["cpf"], lotacao=admin["lotacao"], celular=admin["celular"]):
                print(f'Usuário "{admin["username"]}" criado com sucesso!')
            else:
                print(f'Erro ao tentar criar usuário "{admin["username"]}"')
        else:
            print(f'Admin "{admin["username"]}" já cadastrado.')

if __name__ == '__main__':
    pass