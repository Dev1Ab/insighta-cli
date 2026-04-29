import click
from .auth import login, logout, whoami
from .profiles import profiles

@click.group()
def cli():
    """Insighta CLI"""
    pass

cli.add_command(login)
cli.add_command(logout)
cli.add_command(whoami)
cli.add_command(profiles)