from database.models import db, Nist, Alerta
from app import app
from datetime import datetime, timedelta


with app.app_context() as context:
    nists = Nist.query.limit(3).all()

    novos_alertas = []
    for index, nist in enumerate(nists, start=1):
        novo_alerta = Alerta(
            sq_alerta_restricao=index,
            sq_tipo_alerta_restricao=13,
            tp_status=1,
            no_qualificado=nist.no_pessoa,
            dt_nascimento=nist.dt_nascimento,
            no_mae=nist.no_mae,
            no_pai=nist.no_pai,
            nr_cpf=nist.nr_cpf,
            dt_atualizacao_alerta_restricao=datetime.now() - timedelta(days=1),
            dt_atualizacao_qualificado=datetime.now() - timedelta(days=1),
            dt_download=datetime.now() - timedelta(days=2)
            )
        novos_alertas.append(novo_alerta)

    db.session.add_all(novos_alertas)
    db.session.commit()