from datetime import datetime
import re

import click
from .api import request


@click.group()
def profiles():
    pass


def handle_response(res):
    try:
        data = res.json()
    except ValueError:
        click.echo("Error: server did not return JSON")
        click.echo(res.text)
        raise click.Abort()

    if res.status_code >= 400:
        click.echo(f"Error: {data.get('message', 'Request failed')}")
        raise click.Abort()

    return data


def print_table(items):
    rows = [("ID", "Name", "Gender", "Age", "Age Group", "Country")]

    for p in items:
        rows.append((
            str(p["id"]),
            p["name"],
            p["gender"],
            str(p["age"]),
            p["age_group"],
            p.get("country_name") or p.get("country", {}).get("name", ""),
        ))

    widths = [max(len(str(row[i])) for row in rows) for i in range(len(rows[0]))]

    for idx, row in enumerate(rows):
        click.echo("  ".join(str(col).ljust(widths[i]) for i, col in enumerate(row)))
        if idx == 0:
            click.echo("  ".join("-" * widths[i] for i in range(len(row))))


@profiles.command("list")
@click.option("--gender")
@click.option("--country", "country_id")
@click.option("--age-group")
@click.option("--sort-by")
@click.option("--order", type=click.Choice(["asc", "desc"]))
@click.option("--min-age", type=int)
@click.option("--max-age", type=int)
@click.option("--page", default=1)
@click.option("--limit", default=10)
def list_profiles(**params):
    params = {k: v for k, v in params.items() if v is not None}

    with click.progressbar(length=1, label="Fetching profiles") as bar:
        res = request("GET", "/api/profiles", params=params)
        bar.update(1)

    data = handle_response(res)
    print_table(data["data"])


@profiles.command("get")
@click.argument("id")
def get_profile(id):
    with click.progressbar(length=1, label="Fetching profile") as bar:
        res = request("GET", f"/api/profiles/{id}")
        bar.update(1)

    data = handle_response(res)
    profile = data["data"]

    print_table([profile])


@profiles.command("search")
@click.argument("query")
def search_profiles(query):
    with click.progressbar(length=1, label="Searching profiles") as bar:
        res = request("GET", "/api/profiles/search", params={"q": query})
        bar.update(1)

    data = handle_response(res)
    print_table(data["data"])


@profiles.command("create")
@click.option("--name", required=True)
def create_profile(name):
    with click.progressbar(length=1, label="Creating profile") as bar:
        res = request("POST", "/api/profiles", json={"name": name})
        bar.update(1)

    data = handle_response(res)
    click.echo("Profile created successfully")
    print_table([data["data"]])


@profiles.command("export")
@click.option("--format", default="csv")
@click.option("--gender")
@click.option("--country", "country_id")
def export_profiles(format, gender, country_id):
    params = {
        "format": format,
        "gender": gender,
        "country_id": country_id,
    }
    params = {k: v for k, v in params.items() if v is not None}

    with click.progressbar(length=1, label="Exporting profiles") as bar:
        res = request("GET", "/api/profiles/export", params=params)
        bar.update(1)

    if res.status_code >= 400:
        try:
            data = res.json()
            click.echo(f"Error: {data.get('message', 'Export failed')}")
        except ValueError:
            click.echo("Error: export failed")
            click.echo(res.text)
        raise click.Abort()

    cd = res.headers.get("Content-Disposition")
    if cd:
        fname_match = re.findall('filename="(.+)"', cd)
        if fname_match:
            filename = fname_match[0]
        else:
            filename = f"profiles_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    else:
        filename = f"profiles_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"

    with open(filename, "wb") as f:
        f.write(res.content)

    click.echo(f"Exported to {filename}")