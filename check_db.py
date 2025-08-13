# check_db.py
# Lista tabelas e conta linhas sem precisar de psql
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

load_dotenv()
engine = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)

with engine.connect() as conn:
    insp = inspect(conn)
    tables = insp.get_table_names(schema="public")
    print("Tabelas no schema public:")
    for t in tables:
        try:
            count = conn.execute(text(f'SELECT COUNT(*) FROM "{t}"')).scalar()
        except Exception:
            count = "n/a"
        print(f" - {t} (linhas: {count})")
