import os
import reflex as rx
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.routing import Route
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from urllib.parse import urlencode

load_dotenv()

oauth = OAuth()
oauth.register(
    name="keycloak",
    client_id=os.environ.get("KEYCLOAK_CLIENT_ID"),
    client_secret=os.environ.get("KEYCLOAK_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=(
        f'http://{os.environ.get("KEYCLOAK_DOMAIN")}/realms/'
        f'{os.environ.get("KEYCLOAK_REALM")}/.well-known/openid-configuration'
    ),
)

def index():
    return rx.text("Hello there! You are logged in.")

async def login_endpoint(request: Request):
    callback_uri = request.url_for("callback_endpoint")
    return await oauth.keycloak.authorize_redirect(request, callback_uri)

async def callback_endpoint(request: Request):
    if "user_token" not in request.session:
        return RedirectResponse("/login")

    token = await oauth.keycloak.authorize_access_token(request)
    request.session["user_token"] = token["access_token"]
    return RedirectResponse(url="http://172.31.0.153:3000/")

async def logout_endpoint(request: Request):
    request.session.clear()
    login_url = request.url_for("login_endpoint")
    params = {
        "client_id": os.environ.get("KEYCLOAK_CLIENT_ID"),
        "post_logout_redirect_uri": login_url,
    }
    logout_url = (
        f'http://{os.environ.get("KEYCLOAK_DOMAIN")}/realms/'
        f'{os.environ.get("KEYCLOAK_REALM")}/protocol/openid-connect/logout?'
        + urlencode(params)
    )
    return RedirectResponse(url=logout_url)


def page():
    return rx.cond(
            AuthState.check_auth,
            rx.text("logged in..."),
            rx.text("not logged in :(..."),
        )

async def auth_check(request: Request, next: str = "http://localhost:3000/"):
    if "user_token" not in request.session:
        return RedirectResponse('/login')
    else:
        return RedirectResponse(url=next)

class AuthState(rx.State):
    def check_auth(self):
        # next_url = "http://localhost:3000/protected"
        # q = urlencode({"next": next_url})
        print('working')
        # return rx.redirect(f"http://localhost:8000/auth-check?{q}")
        return True


app = rx.App()
app.api.add_middleware(
    SessionMiddleware, secret_key=os.environ.get("APP_SECRET_KEY", "mydefaultsecret")
)
app.add_page(index) 
app.add_page(page)
app.api.add_route("/login", login_endpoint, methods=["GET"])
app.api.add_route("/callback", callback_endpoint, methods=["GET"])
app.api.add_api_route("/logout", logout_endpoint, methods=["GET"])
app.api.add_api_route('/auth-check', auth_check, methods=['GET'])