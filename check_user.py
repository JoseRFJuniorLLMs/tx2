# check_db_structure_remote.py
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# -----------------------------
# Carrega variáveis do .env
# -----------------------------
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("[ERRO] Variável DATABASE_URL não encontrada no .env")
    exit(1)

engine = create_engine(DATABASE_URL, echo=True)  # echo=True mostra todas queries


# -----------------------------
# Funções de teste
# -----------------------------
def check_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("[OK] Conexão com o banco de dados estabelecida")
    except SQLAlchemyError as e:
        print("[ERRO] Não foi possível conectar ao banco:", e)
        return False
    return True


def check_schema(schema_name):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = :schema
            """), {"schema": schema_name})
            if result.fetchone():
                print(f"[OK] Schema '{schema_name}' existe")
                return True
            else:
                print(f"[ERRO] Schema '{schema_name}' NÃO existe")
                return False
    except SQLAlchemyError as e:
        print("[ERRO] Falha ao consultar schema:", e)
        return False


def check_table(schema_name, table_name):
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema AND table_name = :table
            """), {"schema": schema_name, "table": table_name})
            if result.fetchone():
                print(f"[OK] Tabela '{schema_name}.{table_name}' existe")
                return True
            else:
                print(f"[ERRO] Tabela '{schema_name}.{table_name}' NÃO existe")
                return False
    except SQLAlchemyError as e:
        print("[ERRO] Falha ao consultar tabela:", e)
        return False


def check_user(schema_name, table_name, email):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT * FROM {schema_name}.{table_name} WHERE email = :email
            """), {"email": email})
            user = result.fetchone()
            if user:
                print(f"[OK] Usuário '{email}' encontrado:", dict(user._mapping))
            else:
                print(f"[ERRO] Usuário '{email}' NÃO encontrado")
    except SQLAlchemyError as e:
        print("[ERRO] Falha ao consultar usuário:", e)


# -----------------------------
# Execução
# -----------------------------
if __name__ == "__main__":
    print("===== TESTE DE BANCO DE DADOS REMOTO =====")

    if not check_connection():
        exit(1)

    schema = "backend"
    table = "users"

    if not check_schema(schema):
        exit(1)

    if not check_table(schema, table):
        exit(1)

    test_email = input("Digite o email do usuário para testar: ").strip()
    check_user(schema, table, test_email)
