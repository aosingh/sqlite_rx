import logging.config

import click
import platform

from pprint import pformat

from sqlite_rx import get_default_logger_settings, __version__
from sqlite_rx.client import SQLiteClient


LOG = logging.getLogger(__name__)


@click.command()
@click.version_option(__version__, '-v', '--version', message='%(version)s')
@click.argument('--query', 'Query string to execute')
@click.option('--debug/--no-debug', help='True to enable debugging mode, else False',
              default=False, show_default=True)
@click.option('--connect-address', default='tcp://0.0.0.0:5000',
              help='Address on which to connect to the SQLiteServer',
              show_default=True)
@click.option('--exec-many/--no-exec-many',
              help='True if you want to insert multiple records',
              default=False, show_default=True)
@click.option('--exec-script/--no-exec-script',
              help='True if you want to execute multiple SQL statements in one call',
              default=False, show_default=True)
@click.option('--curvezmq/--no-curvezmq',
              help='True if you want to enable CurveZMQ encryption',
              default=False, show_default=True)
@click.option('--curve-dir', help='Curve Key directory', default=None)
def main(query, debug, connect_address,
         exec_many, exec_script,  curvezmq, curve_dir, ):
    pass
