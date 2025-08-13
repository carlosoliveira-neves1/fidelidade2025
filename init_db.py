# init_db.py
# Cria as tabelas no Postgres usando os modelos do projeto
import os
from dotenv import load_dotenv
load_dotenv()

# Garante que o driver psycopg2 está instalado
try:
    import psycopg2  # noqa
except Exception as e:
    print("Aviso: instale o driver: pip install psycopg2-binary")
    pass

from src.main import app  # carrega o Flask app e configurações
from src.models.user import db  # importa a instância do SQLAlchemy e modelos

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print("✅ Tabelas criadas/atualizadas com sucesso!")
