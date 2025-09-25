# main.py
import os
import uuid
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv
import httpx

# SQLAlchemy
from sqlalchemy import Column, String, create_engine
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# -----------------------------
# Configurações
# -----------------------------
load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

templates = Jinja2Templates(directory="static/")

# -----------------------------
# Banco de dados
# -----------------------------
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Substituindo bcrypt por argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "backend"}  # usa schema backend
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=True)

# Base.metadata.create_all(engine)  # descomente na primeira execução

# -----------------------------
# Utils
# -----------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# -----------------------------
# Rotas
# -----------------------------
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("pages/login/login.html", {"request": request})

@app.get("/welcome")
async def welcome(request: Request):
    name = request.session.get("user_name", "Guest")
    return templates.TemplateResponse("pages/welcome/welcome.html", {"request": request, "name": name})

# -----------------------------
# Google OAuth
# -----------------------------
@app.get("/api/authentication/login")
async def login_google(request: Request):
    redirect_uri = str(request.url_for("auth_callback"))
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={redirect_uri}&"
        f"response_type=code&"
        f"scope=openid email profile"
    )
    return RedirectResponse(url=google_auth_url)

@app.get("/api/authentication/callback")
async def auth_callback(code: str, request: Request):
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter")

    token_url = "https://oauth2.googleapis.com/token"
    redirect_uri = str(request.url_for("auth_callback"))

    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=data)
        resp.raise_for_status()
        token_resp = resp.json()

    id_token_value = token_resp.get("id_token")
    if not id_token_value:
        raise HTTPException(status_code=400, detail="Missing id_token in response")

    try:
        id_info = id_token.verify_oauth2_token(
            id_token_value, google_requests.Request(), GOOGLE_CLIENT_ID
        )
        request.session["user_name"] = id_info.get("name")
        return RedirectResponse(url="/welcome")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {e}")

# -----------------------------
# Login Email/Senha
# -----------------------------
@app.post("/login/email")
async def login_email(request: Request, email: str = Form(...), password: str = Form(...)):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        print("User from DB:", user)  # -> Verifica se encontrou o usuário
        if user:
            print("Password valid?", verify_password(password, user.hashed_password))  # -> True ou False

        if not user or not verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "pages/login/login.html",
                {"request": request, "error": "Email ou senha inválidos"}
            )
        request.session["user_name"] = user.name or user.email
        return RedirectResponse(url="/welcome")
    finally:
        db.close()
