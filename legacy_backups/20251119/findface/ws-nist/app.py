from flask import Flask, jsonify, send_file
from database.models import db
from flask_migrate import Migrate
from pathlib import Path
import os
from routes.api.v1.route_upload_nist import bp_upload_nist
from config_app import *


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}/postgres'

# Do not track modifications
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['UPLOAD_FOLDER'] = './download'

db.init_app(app)

# Flask Alembic
# assuming app and db are your Flask and SQLAlchemy instances respectively
migrate = Migrate(app, db)

app.register_blueprint(bp_upload_nist)  # Register the Blueprint

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5001)