from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func, event, Index, or_
from sqlalchemy.orm import relationship, attributes, aliased
from datetime import datetime, date
from decimal import Decimal

db = SQLAlchemy()

def model_to_dict(model, joined_load=False) -> dict:
    item = {}
    for c in model.__table__.columns:
        if isinstance(getattr(model, c.name), (datetime, date)):
            item[c.name] = getattr(model, c.name).isoformat()
        elif isinstance(getattr(model, c.name), Decimal):
            item[c.name] = float(getattr(model, c.name))
        else:
            item[c.name] = getattr(model, c.name)

    if joined_load:
        relationships = model.__mapper__.relationships.keys()
        for relationship_name in relationships:
            relationship_value = getattr(model, relationship_name)
            if isinstance(relationship_value, list):
                item[relationship_name] = [child.to_dict(joined_load=True) for child in relationship_value]
            else:
                item[relationship_name] = relationship_value.to_dict(joined_load=True) if relationship_value else None

    return item

class AlertaNist(db.Model):
    __tablename__ = 'tb_alerta_nist'
    __table_args__ = (
        UniqueConstraint('id_nist', 'id_alerta', name='uq_alerta_nist'),
        Index('ix_alerta_nist', 'id_nist', 'id_alerta'),
        {'schema': 'findface'},
    )

    id_alerta_nist = db.Column(db.Integer, primary_key=True)
    id_nist = db.Column(db.Integer, db.ForeignKey('findface.tb_nist.id_nist', ondelete="CASCADE"), nullable=False, index=True)
    id_alerta = db.Column(db.Integer, db.ForeignKey('findface.tb_alerta.id_alerta', ondelete="CASCADE"), nullable=False, index=True)

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class AlertaNistFindface(db.Model):
    __tablename__ = 'tb_alerta_nist_findface'
    __table_args__ = (
        Index('ix_alerta_nist_findface_ids', 'id_alerta_nist', 'id_findface'),
        Index('ix_alerta_nist_findface_all', 'id_alerta_nist', 'id_findface', 'card_id'),
        {'schema': 'findface'}
    )

    id_alerta_nist_findface = db.Column(db.Integer, primary_key=True)
    id_alerta_nist = db.Column(db.Integer, db.ForeignKey('findface.tb_alerta_nist.id_alerta_nist', ondelete="CASCADE"), nullable=False, index=True)
    id_findface = db.Column(db.Integer, db.ForeignKey('findface.tb_findface.id_findface', ondelete="CASCADE"), nullable=False, index=True)
    card_id = db.Column(db.Integer, nullable=True, index=True)

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class NistFindface(db.Model):
    __tablename__ = 'tb_nist_findface'
    __table_args__ = (
        UniqueConstraint('id_nist', 'id_findface', name='uq_nist_findface'),
        Index('ix_nist_findface', 'id_nist', 'id_findface'),
        {'schema': 'findface'},
    )

    id_nist_findface = db.Column(db.Integer, primary_key=True)
    id_nist = db.Column(db.Integer, db.ForeignKey('findface.tb_nist.id_nist', ondelete="CASCADE"), nullable=False, index=True)
    id_findface = db.Column('id_findface', db.Integer, db.ForeignKey('findface.tb_findface.id_findface', ondelete="CASCADE"), nullable=False, index=True)
    card_id = db.Column(db.Integer, nullable=True, index=True)

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class Nist(db.Model):
    __tablename__ = 'tb_nist'
    __table_args__ = (
        Index('ix_tb_nist_no_pessoa_dt_nascimento_no_mae', 'no_pessoa', 'dt_nascimento', 'no_mae'),
        Index('ix_tb_nist_no_pessoa_dt_nascimento_no_pai', 'no_pessoa', 'dt_nascimento', 'no_pai'),
        {'schema': 'findface'}
    )
    
    id_nist = db.Column(db.Integer, primary_key=True)
    no_pessoa = db.Column(db.String(250), nullable=False, index=True)
    no_social = db.Column(db.String(250), nullable=True, index=True)
    dt_nascimento = db.Column(db.Date, nullable=True, index=True)
    tp_sexo = db.Column(db.String(1), nullable=True, index=True)
    no_mae = db.Column(db.String(250), nullable=True, index=True)
    no_pai = db.Column(db.String(250), nullable=True, index=True)
    ds_naturalidade = db.Column(db.String(150), nullable=True, index=True)
    ds_pais_nacionalidade = db.Column(db.String(150), nullable=True, index=True)
    nr_cpf = db.Column(db.String(11), nullable=True, index=True)
    nr_rnm = db.Column(db.String(30), nullable=True, index=True)
    nr_passaporte = db.Column(db.String(30), nullable=True, index=True)
    uri_nist = db.Column(db.String(1000), nullable=True, index=True, unique=True)
    nr_mandado_prisao = db.Column(db.String(250), nullable=True, index=True)
    id_base_origem = db.Column(db.Integer, db.ForeignKey('findface.tb_base_origem.id_base_origem', ondelete="CASCADE"), nullable=True, index=True)
    ativo = db.Column(db.Boolean, nullable=False, index=True, default=True)
    dt_atualizacao = db.Column(db.DateTime, nullable=False, index=True, default=lambda: datetime.now())
    md5_hash = db.Column(db.String(250), nullable=False, index=True)

    base_origem = db.relationship('BaseOrigem', backref='nists')
    alertas = db.relationship('Alerta', secondary='findface.tb_alerta_nist', back_populates='nists')
    findfaces = db.relationship('Findface', secondary='findface.tb_nist_findface', back_populates='nists')

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class Alerta(db.Model):
    __tablename__ = 'tb_alerta'
    __table_args__ = (
        Index('ix_tb_alerta_no_qualificado_dt_nascimento_no_mae', 'no_qualificado', 'dt_nascimento', 'no_mae'),
        Index('ix_tb_alerta_no_qualificado_dt_nascimento_no_pai', 'no_qualificado', 'dt_nascimento', 'no_pai'),
        {'schema': 'findface'}
    )

    id_alerta = db.Column(db.Integer, primary_key=True)
    sq_alerta_restricao = db.Column(db.Integer, nullable=False, index=True)
    sq_tipo_alerta_restricao = db.Column(db.Integer, nullable=False, index=True)
    tp_status = db.Column(db.Integer, nullable=False, index=True)
    no_qualificado = db.Column(db.String(250), nullable=False, index=True)
    dt_nascimento = db.Column(db.Date, nullable=True, index=True)
    no_mae = db.Column(db.String(250), nullable=True, index=True)
    no_pai = db.Column(db.String(250), nullable=True, index=True)
    nr_cpf = db.Column(db.String(11), nullable=True, index=True)
    dt_atualizacao_alerta_restricao = db.Column(db.DateTime, nullable=False, index=True)
    dt_atualizacao_qualificado = db.Column(db.DateTime, nullable=False, index=True)
    nr_mandado_prisao = db.Column(db.String(250), nullable=True, index=True)
    dt_download = db.Column(db.DateTime, nullable=False, index=True)

    nists = relationship('Nist', secondary='findface.tb_alerta_nist', back_populates='alertas')

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class Findface(db.Model):
    __tablename__ = 'tb_findface'
    __table_args__ = {'schema': 'findface'}

    id_findface = db.Column(db.Integer, primary_key=True)
    no_findface = db.Column(db.String(50), nullable=False, unique=True)
    url_base = db.Column(db.String(500), nullable=False)

    base_origens = db.relationship('BaseOrigem', secondary='findface.tb_baseorigem_findface', back_populates='findfaces')
    nists = db.relationship('Nist', secondary='findface.tb_nist_findface', back_populates='findfaces')
    alerta_nist_findfaces = db.relationship('AlertaNistFindface', backref='findface', lazy='dynamic')

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class BaseOrigem(db.Model):
    __tablename__ = 'tb_base_origem'
    __table_args__ = {'schema': 'findface'}

    id_base_origem = db.Column(db.Integer, primary_key=True)
    no_base_origem = db.Column(db.String(50), nullable=False, index=True)
    ativo = db.Column(db.Boolean, nullable=False, index=True, default=True)

    findfaces = db.relationship('Findface', secondary='findface.tb_baseorigem_findface', back_populates='base_origens')

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class BaseOrigemFindface(db.Model):
    __tablename__ = 'tb_baseorigem_findface'
    __table_args__ = {'schema': 'findface'}

    id_base_origem = db.Column(db.Integer, db.ForeignKey('findface.tb_base_origem.id_base_origem', ondelete="CASCADE"), primary_key=True)
    id_findface = db.Column(db.Integer, db.ForeignKey('findface.tb_findface.id_findface', ondelete="CASCADE"), primary_key=True)

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class TipoLog(db.Model):
    __tablename__ = 'tb_tipo_log'
    __table_args__ = {'schema': 'findface'}
    
    id_tipo_log = db.Column(db.Integer, primary_key=True)
    cd_tipo_log = db.Column(db.Integer, nullable=False, index=True, unique=True)
    ds_tipo_log = db.Column(db.String(150), nullable=True, index=True)

    logs = db.relationship('Log', backref='tipo_log', lazy='dynamic')

class Log(db.Model):
    __tablename__ = 'tb_log'
    __table_args__ = {'schema': 'findface'}

    id_log = db.Column(db.Integer, primary_key=True)
    id_origem = db.Column(db.Integer, nullable=True, index=True)
    cd_tipo_log = db.Column(db.Integer, db.ForeignKey('findface.tb_tipo_log.cd_tipo_log', ondelete="CASCADE"), nullable=False, index=True)
    ds_log = db.Column(db.Text, nullable=True)
    dt_log = db.Column(db.DateTime, nullable=False, index=True, default=lambda: datetime.now())
