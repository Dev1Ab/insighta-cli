import click
import webbrowser
import secrets
import hashlib
import base64
import requests
import time
from http.server import HTTPServer, BaseHTTPRequestHandler

from .config import load_tokens, save_tokens, clear_tokens

BASE_URL = "http://127.0.0.1:8000"


@click.command()
def login():
    """Login via GitHub OAuth"""

    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode()).digest()
    ).decode().rstrip("=")

    state = f"cli:{secrets.token_urlsafe(32)}"

    redirect_uri = "http://localhost:8765/callback"

    auth_url = f"{BASE_URL}/auth/github?state={state}&code_challenge={code_challenge}"

    code_holder = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            from urllib.parse import urlparse, parse_qs


            query = parse_qs(urlparse(self.path).query)
            code_holder["code"] = query.get("code")[0]
            code_holder["state"] = query.get("state")[0]
            
            if code_holder["state"] != state:
                raise Exception("State mismatch!")

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Login successful. You can close this tab.")

    server = HTTPServer(("localhost", 8765), Handler)

    webbrowser.open(auth_url)
    click.echo("Opening browser for authentication...")

    server.handle_request()

    # Exchange code
    res = requests.post(f"{BASE_URL}/auth/exchange", json={
        "code": code_holder["code"],
        "code_verifier": code_verifier
    })

    if res.status_code != 200:
        click.echo("Login failed.")
        click.echo(f"Status: {res.status_code}")
        # click.echo(res.text)
        return

    try:
        data = res.json()
    except ValueError:
        click.echo("Backend did not return JSON.")
        click.echo(f"Status: {res.status_code}")
        click.echo(res.text)
        return

    save_tokens({
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": time.time() + 180
    })

    click.echo(f"Logged in as @{data['username']}")


@click.command()
def logout():
    tokens = load_tokens()
    requests.post(f"{BASE_URL}/auth/logout", json={
        "refresh_token": tokens["refresh_token"]
    })
    clear_tokens()
    click.echo("Logged out.")


@click.command()
def whoami():
    from .api import request
    res = request("GET", "/auth/me")
    click.echo(res.json()["username"])