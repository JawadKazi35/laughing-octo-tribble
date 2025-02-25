"""Welcome to Reflex! This file outlines the steps to create a basic app."""

import reflex as rx
from rxconfig import config
from kinde_sdk import Configuration
from kinde_sdk.kinde_api_client import GrantType, KindeApiClient
import os

# Kinde configuration
KINDE_HOST = os.environ.get("KINDE_HOST", "https://your_domain.kinde.com")
KINDE_CLIENT_ID = os.environ.get("KINDE_CLIENT_ID", "your_client_id")
KINDE_CLIENT_SECRET = os.environ.get("KINDE_CLIENT_SECRET", "your_client_secret")
KINDE_REDIRECT_URL = os.environ.get("KINDE_REDIRECT_URL", "http://localhost:3000")
KINDE_POST_LOGOUT_REDIRECT_URL = os.environ.get("KINDE_POST_LOGOUT_REDIRECT_URL", "http://localhost:3000")

configuration = Configuration(host=KINDE_HOST)
kinde_api_client_params = {
    "configuration": configuration,
    "domain": KINDE_HOST,
    "client_id": KINDE_CLIENT_ID,
    "client_secret": KINDE_CLIENT_SECRET,
    "grant_type": GrantType.AUTHORIZATION_CODE,
    "callback_url": KINDE_REDIRECT_URL
}
kinde_client = KindeApiClient(**kinde_api_client_params)

class State(rx.State):
    """The app state."""

    is_authenticated: bool = False
    user_details: dict = {}
    auth_code: str = ""
    auth_state: str = ""
    auth_attempted: bool = False 

    def login(self):
        print("Login called")
        return rx.redirect(kinde_client.get_login_url())

    def logout(self):
        print("Logout called")
        self.is_authenticated = False
        self.user_details = {}
        self.auth_code = ""
        self.auth_state = ""
        self.auth_attempted = False
        return rx.redirect(kinde_client.logout(redirect_to=KINDE_POST_LOGOUT_REDIRECT_URL))

    def check_auth(self):
        print(f"check_auth called. auth_code: {self.auth_code}, auth_state: {self.auth_state}")
        if self.auth_code and self.auth_state and not self.auth_attempted:
            try:
                self.auth_attempted = True 
                full_url = f"{KINDE_REDIRECT_URL}?code={self.auth_code}&state={self.auth_state}"
                print(f"Attempting to fetch token with URL: {full_url}")
                kinde_client.fetch_token(authorization_response=full_url)
                self.auth_attempted = True
                print("Token fetched successfully")
                
                self.is_authenticated = kinde_client.is_authenticated()
                print(f"is_authenticated: {self.is_authenticated}")
                
                if self.is_authenticated:
                    self.user_details = kinde_client.get_user_details()
                    print(f"User details: {self.user_details}")
                
                self.auth_code = ""
                self.auth_state = ""
                print("Redirecting to /")
                return rx.redirect("/")
            except Exception as e:
                print(f"Authentication error: {str(e)}")
                print(f"Error type: {type(e)}")

        else:
            print("No auth_code or auth_state present, or auth already attempted")
        return rx.redirect("/")

    def handle_auth(self):
        print("handle_auth called")
        if not self.auth_attempted:
            auth_params = self.router.page.params
            print(f"Query params: {auth_params}")
            if auth_params.get('code') and auth_params.get('state'):
                print("Code and state found in query params")
                self.auth_code = auth_params['code']
                self.auth_state = auth_params['state']
                return self.check_auth()
        else:
            print("Auth already attempted, skipping")

def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Welcome to Reflex!", size="9"),
            rx.text(
                "Get started by editing ",
                rx.code(f"{config.app_name}/{config.app_name}.py"),
                size="5",
            ),
            rx.link(
                rx.button("Check out our docs!"),
                href="https://reflex.dev/docs/getting-started/introduction/",
                is_external=True,
            ),
            rx.cond(
                State.is_authenticated,
                rx.vstack(
                    rx.text(f"Welcome, {State.user_details['given_name']}!"),
                    rx.button("Logout", on_click=State.logout),
                ),
                rx.button("Login", on_click=State.login),
            ),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
        rx.logo(),
        on_mount=State.handle_auth,
    )

app = rx.App()
app.add_page(index)