# update_password.py
from sqlalchemy import create_engine, text
from passlib.context import CryptContext

# Hash de senha com Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# URL do banco (pode manter a mesma)
DATABASE_URL = "postgresql://postgres:Debian23@aurora-database-dev.crog6c44iprj.eu-west-2.rds.amazonaws.com:5432/aurora-database-dev"

# Conexão
engine = create_engine(DATABASE_URL)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def update_password(email: str, new_password: str):
    hashed = hash_password(new_password)
    with engine.connect() as conn:
        result = conn.execute(
            text("UPDATE backend.users SET hashed_password = :hashed WHERE email = :email"),
            {"hashed": hashed, "email": email}
        )
        conn.commit()
        if result.rowcount == 0:
            print(f"Usuário {email} não encontrado.")
        else:
            print(f"Senha do usuário {email} atualizada com sucesso!")

if __name__ == "__main__":
    # Atualiza a senha para web2ajax@gmail.com
    update_password("web2ajax@gmail.com", "debian23")
