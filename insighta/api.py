import requests
import time
import click
from .config import load_tokens, save_tokens, is_expired


BASE_URL = "http://127.0.0.1:8000"


def refresh_token(tokens):
    res = requests.post(f"{BASE_URL}/auth/refresh", json={
        "refresh_token": tokens["refresh_token"]
    })

    if res.status_code != 200:
        return None

    data = res.json()
    tokens["access_token"] = data["access_token"]
    tokens["expires_at"] = time.time() + 180
    save_tokens(tokens)
    return tokens


def get_headers():
    tokens = load_tokens()

    if not tokens:
        click.echo("Not logged in. Please run: insighta login")
        raise click.Abort()

    if is_expired(tokens):
        tokens = refresh_token(tokens)
        if not tokens:
            click.echo("Session expired. Please run: insighta login")
            raise click.Abort()

    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-API-Version": "1",
    }

def request(method, path, **kwargs):
    headers = get_headers()
    res = requests.request(method, f"{BASE_URL}{path}", headers=headers, **kwargs)

    if res.status_code == 401:
        click.echo("Unauthorized")

    return res