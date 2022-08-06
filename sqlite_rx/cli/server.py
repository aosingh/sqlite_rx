import logging.config

import typing
import platform

from pprint import pformat

import click
import rich.console
import rich.markup
import rich.progress
import rich.syntax
import rich.table

from sqlite_rx import get_default_logger_settings, __version__
from sqlite_rx.server import SQLiteServer


LOG = logging.getLogger(__name__)


def print_help():
    console = rich.console.Console()
    console.print(f"[bold]sqlite-server[/bold]   :paw_prints:", justify="center")
    console.print()
    console.print("A simple, fast and secure server for the SQLite database.", justify="center")
    console.print()
    console.print("Usage: [bold]sqlite-server[/bold] [cyan][OPTIONS][/cyan] ", justify="left")
    console.print()
    table = rich.table.Table.grid(padding=1, pad_edge=True)
    table.add_column("Parameter", no_wrap=True, justify="left", style="bold")
    table.add_column("Description")
    table.add_row("-l, --log-level [cyan]LOG_LEVEL",
                  "CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET\n"
                  "Default value is [bold][cyan]INFO")
    table.add_row('-a, --tcp-address [cyan]tcp://<host>:<port>',
                  "The host and port on which to listen for TCP connections\n"
                  "Default value is [bold][cyan]tcp://0.0.0.0:5000")
    table.add_row("-d --database [cyan]PATH",
                  "Path to the database\n"
                  "You can use :memory: for an in-memory database\n"
                  "Default value is [bold][cyan]:memory:")
    table.add_row("--zap/--no-zap",
                  "Enable/Disable ZAP Authentication\n"
                  "Default value is [bold][cyan]False")
    table.add_row('--curvezmq/--no-curvezmq',
                  "Enable/Disable CurveZMQ\n"
                  "Default value is [bold][cyan]False")
    table.add_row("-c --curve-dir [cyan]PATH",
                  "Path to the Curve key directory\n"
                  "Default value is [bold][cyan]~/.curve")
    table.add_row("-k --key-id [cyan]CURVE KEY ID",
                  "Server's Curve Key ID")
    table.add_row("-b --backup-database [cyan]PATH",
                  "Path to the backup database")
    table.add_row("-i --backup-interval [cyan]FLOAT",
                  "Backup interval in seconds")
    table.add_row("--help", "Show this message and exit.")
    console.print(table)


def handle_help(ctx: click.Context,
                param: typing.Union[click.Option, click.Parameter],
                value: typing.Any) -> None:
    if not value or ctx.resilient_parsing:
        return
    print_help()
    ctx.exit()


@click.command(add_help_option=False)
@click.version_option(__version__, '-v', '--version', message='%(version)s')
@click.option('--log-level',
              '-l',
              default='INFO',
              help="Logging level",
              type=click.Choice("CRITICAL FATAL ERROR WARN WARNING INFO DEBUG NOTSET".split()),
              show_default=True)
@click.option('--tcp-address',
              '-a',
              default='tcp://0.0.0.0:5000',
              type=click.STRING,
              help='The host and port on which to listen for TCP connections',
              show_default=True)
@click.option('--database',
              '-d',
              type=click.STRING,
              default=':memory:',
              help='Path like object giving the database name\n'
                   'You can use `:memory:` for an in-memory database',
              show_default=True)
@click.option('--zap/--no-zap',
              help='True, if you want to enable ZAP authentication',
              default=False,
              show_default=True)
@click.option('--curvezmq/--no-curvezmq',
              help='True, if you want to enable CurveZMQ encryption',
              default=False,
              show_default=True)
@click.option('--curve-dir',
              '-d',
              type=click.Path(exists=True),
              help='Curve Key directory',
              default=None)
@click.option('--key-id',
              '-k',
              type=click.STRING,
              help='Server key ID',
              default=None)
@click.option('--backup-database',
              '-b',
              help='Path to the backup database',
              default=None,
              type=str,
              show_default=True)
@click.option('--backup-interval',
              '-i',
              help='Backup interval in seconds',
              default=600.0,
              type=click.FLOAT,
              show_default=True)
@click.option("--help",
              is_flag=True,
              is_eager=True,
              expose_value=False,
              callback=handle_help,
              help="Show this message and exit.")
def main(log_level,
         tcp_address,
         database,
         zap,
         curvezmq,
         curve_dir,
         key_id,
         backup_database,
         backup_interval):
    logging.config.dictConfig(get_default_logger_settings(level=log_level))
    LOG.info("Python Platform %s", platform.python_implementation())
    kwargs = {
        'bind_address': tcp_address,
        'database': database,
        'curve_dir': curve_dir,
        'use_zap_auth': zap,
        'use_encryption': curvezmq,
        'server_curve_id': key_id,
        'backup_database': backup_database,
        'backup_interval': backup_interval
    }
    LOG.info('Args %s', pformat(kwargs))
    server = SQLiteServer(**kwargs)
    server.start()
    server.join()
