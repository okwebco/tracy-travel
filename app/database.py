from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./control_finanzas.db").strip()

# DEBUG TEMPORAL — ver qué valor tiene DATABASE_URL al arrancar
import sys
print(f"[DB-DEBUG] len={len(DATABASE_URL)} repr={repr(DATABASE_URL[:60])}", file=sys.stderr, flush=True)

# SQLite requiere check_same_thread=False; PostgreSQL no acepta ese parámetro
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping: revalida la conexión antes de usarla (Neon/Postgres cierra las
# conexiones ociosas; sin esto darían errores intermitentes). Inofensivo en SQLite.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
