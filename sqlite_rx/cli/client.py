import logging.config

import typing
import platform

from pprint import pformat

import click
import click_repl
import rich.console
import rich.markup
import rich.progress
import rich.syntax
import rich.table

from rich import print_json

from sqlite_rx import get_default_logger_settings, __version__
from sqlite_rx.client import SQLiteClient


LOG = logging.getLogger(__name__)


def print_help():
    console = rich.console.Console()
    console.print("[bold]sqlite-client :paw_prints:", justify="center")
    console.print()
    console.print("A simple, fast and secure client for the SQLite database.", justify="center")
    console.print()
    console.print("Usage: [bold]sqlite-client [OPTIONS] exec[/bold] [cyan]<query> [/cyan] ", justify="left")
    console.print()
    table = rich.table.Table.grid(padding=1, pad_edge=True)
    table.add_column("Parameter", no_wrap=True, justify="left", style="bold")
    table.add_column("Description")
    table.add_row("-l, --log-level [bold][cyan]LOG_LEVEL",
                  "CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET\n"
                  "Default level is [bold][cyan]CRITICAL")
    table.add_row('-a, --connect-address [bold][cyan]tcp://<host>:<port>',
                  "The host and port on which to connect\n"
                  "Default value is tcp://0.0.0.0:5000")
    table.add_row("--zap/--no-zap",
                  "Enable/Disable ZAP Authentication\n"
                  "Default value is [bold][cyan]False")
    table.add_row('--curvezmq/--no-curvezmq',
                  "Enable/Disable CurveZMQ\n"
                  "Default value is [bold][cyan]False")
    table.add_row("-d --curve-dir [cyan]PATH",
                  "Path to the Curve key directory\n"
                  "Default value is [italic][bold][cyan]~/.curve")
    table.add_row("-c --client-key-id [cyan]CURVE KEY ID",
                  "Client's Curve Key ID")
    table.add_row("--help", "Show this message and exit.")
    console.print(table)


def handle_help(ctx: click.Context,
                param: typing.Union[click.Option, click.Parameter],
                value: typing.Any) -> None:
    if not value or ctx.resilient_parsing:
        return
    print_help()
    ctx.exit()


@click.group(add_help_option=False, invoke_without_command=True)
@click.version_option(__version__, '-v', '--version', message='%(version)s')
@click.option('--log-level',
              '-l',
              default='CRITICAL',
              help="Logging level",
              type=click.Choice("CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET".split()),
              show_default=True)
@click.option('--connect-address',
              '-a',
              default='tcp://0.0.0.0:5000',
              help='Address on which to connect to the SQLiteServer',
              show_default=True)
@click.option('--curvezmq/--no-curvezmq',
              help='True if you want to enable CurveZMQ encryption',
              default=False,
              show_default=True)
@click.option('--curve-dir',
              '-d',
              help='Curve Key directory',
              default=None)
@click.option('--client-key-id',
              '-c',
              type=click.STRING,
              help='Client key ID',
              default=None)
@click.option('--server-key-id',
              '-s',
              type=click.STRING,
              help='Server key ID',
              default=None)
@click.option("--help",
              is_flag=True,
              is_eager=True,
              expose_value=False,
              callback=handle_help,
              help="Show this message and exit.")
@click.pass_context
def main(ctx, log_level, connect_address,  curvezmq, curve_dir, client_key_id, server_key_id):
    logging.config.dictConfig(get_default_logger_settings(level=log_level))
    client = SQLiteClient(connect_address=connect_address,
                          use_encryption=curvezmq,
                          curve_dir=curve_dir,
                          client_curve_id=client_key_id,
                          server_curve_id=server_key_id)
    ctx.obj = client


@main.command(name='exec', add_help_option=False)
@click.argument('query')
@click.option("--help",
              is_flag=True,
              is_eager=True,
              expose_value=False,
              callback=handle_help,
              help="Show this message and exit.")
@click.pass_context
def execute_query(ctx, query):
    client = ctx.obj
    client.execute(query=query)
    result = client.execute(query=query)
    print_json(data=result, indent=2)



