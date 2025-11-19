from flask import Flask, jsonify, send_file
from rotas.reconhecimento_facial import reconhecimento_facial_bp
from rotas.foto import foto_bp
from rotas.pessoas import pessoas_bp
from rotas.raiz import raiz_bp

app = Flask(__name__)

app.register_blueprint(reconhecimento_facial_bp)
app.register_blueprint(foto_bp)
app.register_blueprint(pessoas_bp)
app.register_blueprint(raiz_bp)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=6000)