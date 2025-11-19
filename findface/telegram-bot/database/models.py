from flask_sqlalchemy import SQLAlchemy
import json
from datetime import datetime
from decimal import Decimal
from sqlalchemy import CheckConstraint, func, event, Index, or_
from sqlalchemy.orm import relationship, attributes, aliased


db = SQLAlchemy()

def model_to_dict(model, joined_load=False) -> dict:
    
    item = {}
    for c in model.__table__.columns:
        # Se o field for do tipo datatime, converte para texto no formato ISO
        if isinstance(getattr(model, c.name), (datetime, date)):
            item[c.name] = getattr(model, c.name).isoformat()
        elif isinstance(getattr(model, c.name), Decimal):
            # Convert Decimal to a float or string (choose based on your precision needs)
            item[c.name] = float(getattr(model, c.name))
        else:
            item[c.name] = getattr(model, c.name)

    # Handle relationships
    if joined_load:
        relationships = model.__mapper__.relationships.keys()
        for relationship_name in relationships:
            relationship_value = getattr(model, relationship_name)
            if isinstance(relationship_value, list):
                item[relationship_name] = [child.to_dict(joined_load=True) for child in relationship_value]
            else:
                item[relationship_name] = relationship_value.to_dict(joined_load=True) if relationship_value else None

    return item


class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, index=True, nullable=False)
    perfil = db.Column(db.Integer, index=True, comment='1-Administrador, 2-Usuario', nullable=False)
    criador = db.Column(db.String(32), index=True, nullable=False)
    data_criacao = db.Column(db.DateTime, index=True, nullable=False)
    cpf = db.Column(db.String(11), index=True, nullable=False)
    lotacao = db.Column(db.String(100), index=True, nullable=False)
    celular = db.Column(db.String(30), index=True, nullable=False)

    def to_dict(self, joined_load=False):
        return model_to_dict(self)

class UsuarioLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data_criacao = db.Column(db.DateTime, index=True, nullable=False, default=lambda: datetime.now())
    username = db.Column(db.Integer, db.ForeignKey('usuario.username'), nullable=False, index=True)
    ds_log = db.Column(db.Text)

    usuario = db.relationship('Usuario', backref=db.backref('logs', lazy=True))

    def to_dict(self, joined_load=False):
        return model_to_dict(self)
