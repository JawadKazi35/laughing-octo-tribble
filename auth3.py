import reflex as rx
from dotenv import load_dotenv
import os
from keycloak import KeycloakOpenID

load_dotenv()
keycloak_openid = KeycloakOpenID(server_url=os.environ.get('KEYCLOAK_DOMAIN'),
                                 client_id=os.environ.get('KEYCLOAK_CLIENT_ID'),
                                 realm_name=os.environ.get('KEYCLOAK_REALM'),
                                 client_secret_key=os.environ.get('KEYCLOAK_CLIENT_SECRET'))

class State(rx.State):
    token: str = ''
    logged_in: bool = False
    def login(self, form_data: dict):
            _username = form_data['username']
            _password = form_data['password']
            try:
                token = keycloak_openid.token(_username, _password)
                self.token = token['access_token']
                self.logged_in = True
                print('login successful')
                return rx.redirect('/')
            except Exception as e:
                print('login failed, error: ', e)
                return rx.redirect('/login')

    def logout(self):
        self.token = ''
        self.logged_in = False
        rx.redirect('/login')

    def check_auth(self):
        token_info = keycloak_openid.introspect(self.token)
        token_is_active = token_info.get("active", False)
        print('checking auth')
        if token_is_active:
            self.logged_in = True
            rx.redirect('/')
        else:
            self.logged_in = False
            rx.redirect('/login')

@rx.page(route='/')
def index():
    return rx.text('h')

@rx.page(route='/login')
def login():
    return rx.cond(
        State.logged_in,
        rx.text('', on_mount=rx.redirect('/')),
        login_page(),
        
    )

def login_page() -> rx.Component:
    return rx.vstack(   
            rx.form(
                rx.vstack(
                    rx.input(
                        placeholder="username",
                        name="username",
                    ),
                    rx.input(
                        placeholder="password",
                        name="password",
                    ),
                    rx.button("submit", type="submit"),
                ),
                on_submit=State.login,
                reset_on_submit=True,
            ),
        )

@rx.page(route='/logout')
def logout():
    return rx.text('', on_mount=State.logout)

app = rx.App()