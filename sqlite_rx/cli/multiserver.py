import logging.config
import typing
import platform
import json
import os
from pprint import pformat

import click
import rich.console
import rich.markup
import rich.progress
import rich.syntax
import rich.table

from sqlite_rx import get_default_logger_settings, __version__
from sqlite_rx.multiserver import SQLiteMultiServer


LOG = logging.getLogger(__name__)


def print_help():
    console = rich.console.Console()
    console.print(f"[bold]sqlite-multiprocess-server[/bold]   :paw_prints:", justify="center")
    console.print()
    console.print("A multi-process server for SQLite databases, with each database running in its own process.", justify="center")
    console.print()
    console.print("Usage: [bold]sqlite-multiprocess-server[/bold] [cyan][OPTIONS][/cyan] ", justify="left")
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
    table.add_row("-d --default-database [cyan]PATH",
                  "Path to the default database\n"
                  "You can use :memory: for an in-memory database\n"
                  "Default value is [bold][cyan]:memory:")
    table.add_row("-m --database-map [cyan]JSON",
                  "JSON string mapping database names to paths\n"
                  "Example: '{\"db1\": \"/path/to/db1.db\", \"db2\": \"/path/to/db2.db\"}'")
    table.add_row("-b --backup-dir [cyan]PATH",
                  "Directory to store database backups\n"
                  "If not provided, backups will be disabled")
    table.add_row("-i --backup-interval [cyan]SECONDS",
                  "Interval between backups in seconds\n"
                  "Default value is [bold][cyan]600 (10 minutes)")
    table.add_row("-p --base-port [cyan]PORT",
                  "Base port for database processes\n"
                  "Default value is [bold][cyan]6000")
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
    table.add_row("--data-directory [cyan]PATH",
                  "Base directory for database files (if using relative paths)")
    table.add_row("--auto-connect/--no-auto-connect",
                  "Enable/Disable automatic connection to existing databases\n"
                  "Default value is [bold][cyan]False")
    table.add_row("--auto-create/--no-auto-create",
                  "Enable/Disable automatic creation of new databases\n"
                  "Default value is [bold][cyan]False")
    table.add_row("--max-connections [cyan]NUMBER",
                  "Maximum number of dynamic database connections\n"
                  "Default value is [bold][cyan]20")
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
@click.option('--default-database',
              '-d',
              type=click.STRING,
              default=':memory:',
              help='Path to the default database\n'
                   'You can use `:memory:` for an in-memory database',
              show_default=True)
@click.option('--database-map',
              '-m',
              type=click.STRING,
              help='JSON string mapping database names to paths',
              default='{}')
@click.option('--backup-dir',
              '-b',
              type=click.Path(),
              help='Directory to store database backups',
              default=None)
@click.option('--backup-interval',
              '-i',
              type=click.INT,
              help='Interval between backups in seconds',
              default=600,
              show_default=True)
@click.option('--base-port',
              '-p',
              type=click.INT,
              help='Base port for database processes',
              default=6000,
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
              '-c',
              type=click.Path(),
              help='Curve Key directory',
              default=None)
@click.option('--key-id',
              '-k',
              type=click.STRING,
              help='Server key ID',
              default=None)
@click.option('--data-directory',
              type=click.Path(file_okay=False),
              help='Base directory for database files (if using relative paths)',
              default=None)
@click.option('--auto-connect/--no-auto-connect',
              help='Whether to automatically connect to existing databases',
              default=False,
              show_default=True)
@click.option('--auto-create/--no-auto-create',
              help='Whether to automatically create new databases',
              default=False,
              show_default=True)
@click.option('--max-connections',
              type=click.INT,
              help='Maximum number of dynamic database connections',
              default=20,
              show_default=True)
@click.option("--help",
              is_flag=True,
              is_eager=True,
              expose_value=False,
              callback=handle_help,
              help="Show this message and exit.")
def main(log_level,
         tcp_address,
         default_database,
         database_map,
         backup_dir,
         backup_interval,
         base_port,
         zap,
         curvezmq,
         curve_dir,
         key_id,
         data_directory,
         auto_connect,
         auto_create,
         max_connections):
    logging.config.dictConfig(get_default_logger_settings(level=log_level))
    LOG.info("Python Platform %s", platform.python_implementation())
    
    # Parse the database map JSON
    try:
        database_map_dict = json.loads(database_map)
    except json.JSONDecodeError as e:
        LOG.error(f"Failed to parse database map JSON: {e}")
        database_map_dict = {}
    
    # Create backup directory if needed
    if backup_dir and not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        LOG.info(f"Created backup directory: {backup_dir}")
    
    kwargs = {
        'bind_address': tcp_address,
        'default_database': default_database,
        'database_map': database_map_dict,
        'backup_dir': backup_dir,
        'backup_interval': backup_interval,
        'base_port': base_port,
        'curve_dir': curve_dir,
        'use_zap_auth': zap,
        'use_encryption': curvezmq,
        'server_curve_id': key_id,
        'data_directory': data_directory,
        'auto_connect': auto_connect,
        'auto_create': auto_create,
        'max_connections': max_connections
    }
    LOG.info('Args %s', pformat(kwargs))
    
    server = SQLiteMultiServer(**kwargs)
    server.start()
    
    print(f"\nSQLite Multi-Process Server started on {tcp_address}")
    print(f"Default database: {default_database}")
    print(f"Database map: {database_map_dict}")
    print(f"Base port for database processes: {base_port}")
    
    if data_directory:
        print(f"Data directory: {data_directory}")
    
    if backup_dir:
        print(f"Backups enabled: {backup_dir} (every {backup_interval} seconds)")
    else:
        print("Backups disabled")
    
    print(f"Auto-connect: {'Enabled' if auto_connect else 'Disabled'}")
    if auto_connect:
        print(f"Auto-create: {'Enabled' if auto_create else 'Disabled'}")
        print(f"Max dynamic connections: {max_connections}")
    
    print("\nPress Ctrl+C to stop the server.")
    
    try:
        server.join()
    except KeyboardInterrupt:
        print("\nShutting down server...")


if __name__ == "__main__":
    main()