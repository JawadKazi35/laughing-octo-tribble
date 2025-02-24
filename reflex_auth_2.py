import os
import reflex as rx
from dotenv import load_dotenv
from authlib.integrations.starlette_client import OAuth
from starlette.requests import Request
from starlette.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
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

async def login_endpoint(request: Request):
    callback_uri = request.url_for("callback_endpoint")
    return await oauth.keycloak.authorize_redirect(request, callback_uri)

async def callback_endpoint(request: Request):
    token = await oauth.keycloak.authorize_access_token(request)
    request.session["user"] = dict(token)
    return RedirectResponse(url="http://172.31.0.153:3000/")

async def logout_endpoint(request: Request):
    params = {
        "client_id": os.environ.get("KEYCLOAK_CLIENT_ID"),
        "post_logout_redirect_uri": request.url_for("login_endpoint"),
    }
    logout_url = (
        f'http://{os.environ.get("KEYCLOAK_DOMAIN")}/realms/'
        f'{os.environ.get("KEYCLOAK_REALM")}/protocol/openid-connect/logout?'
        + urlencode(params)
    )
    return RedirectResponse(url=logout_url)


class State(rx.State):
    count: int = 0
    authenticated: bool = True
    def increment(self):
        self.count += 1
    def decrement(self):
        self.count -= 1

def index() -> rx.Component:
    return rx.vstack(
        rx.cond(
                State.authenticated,
                page(),
                rx.link("Login via Keycloak", href="/login"),
        )
    )

def page() -> rx.Component:
    return rx.text('you are authenticated')

app = rx.App()
app.add_page(index)

app.api.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("APP_SECRET_KEY", "mydefaultsecret")
)

app.api.add_api_route("/login", login_endpoint, methods=["GET"])
app.api.add_api_route("/callback", callback_endpoint, methods=["GET"])
app.api.add_api_route("/logout", logout_endpoint, methods=["GET"])
