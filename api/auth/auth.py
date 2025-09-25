import os
from urllib.parse import quote
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY", "dev-secret"))

router = APIRouter(prefix="/api/authentication")

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")


@router.get("/login")
async def login(request: Request):
    # URL-encode do redirect_uri
    redirect_uri = str(request.url_for("auth_callback"))
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope=openid email profile"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/callback")
async def auth_callback(code: str = None, request: Request = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' parameter in callback")

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
        raise HTTPException(status_code=400, detail="Missing id_token in response.")

    try:
        id_info = id_token.verify_oauth2_token(id_token_value, google_requests.Request(), GOOGLE_CLIENT_ID)
        request.session["user_name"] = id_info.get("name")
        return {"message": f"Welcome {id_info.get('name')}!"}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid id_token: {e}")
