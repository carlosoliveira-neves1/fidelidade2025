# test_db.py
# Testa a conexão com o Postgres lendo DATABASE_URL do .env
import os
from dotenv import load_dotenv
import sys

load_dotenv()
db_url = os.getenv("DATABASE_URL")
if not db_url:
    print("Erro: DATABASE_URL não encontrado no .env")
    sys.exit(1)

print("Usando DATABASE_URL:", db_url)

# Testa com SQLAlchemy para abrir conexão
from sqlalchemy import create_engine, text

engine = create_engine(db_url, pool_pre_ping=True)

with engine.connect() as conn:
    versao = conn.execute(text("select version();")).scalar()
    print("Conectado! Versão do Postgres:", versao)
