import logging.config

import click

from pprint import pformat

from sqlite_rx import get_default_logger_settings
from sqlite_rx.server import SQLiteServer


LOG = logging.getLogger(__name__)

@click.command()
@click.option('--log-level', default='INFO', help="Logging level", type=click.Choice(list(logging._nameToLevel.keys())), show_default=True)
@click.option('--advertise-host', default='0.0.0.0', help='Host address on which to run the SQLiteServer', show_default=True)
@click.option('--port', default='5000', help="Port on which SQLiteServer will listen for connection requests", type=str, show_default=True)
@click.option('--database', default=':memory:', help='Path like object giving the database name. You can use `:memory:` for an in-memory database', show_default=True)
@click.option('--zap/--no-zap', help='True, if you want to enable ZAP authentication', default=False, show_default=True)
@click.option('--curvezmq/--no-curvezmq', help='True, if you want to enable CurveZMQ encryption', default=False, show_default=True)
@click.option('--curve-dir', help='Curve Key directory', default=None)
@click.option('--key-id', help='Server key ID', default=None)
def main(log_level,
         advertise_host,
         port,
         database,
         zap,
         curvezmq,
         curve_dir,
         key_id):
    logging.config.dictConfig(get_default_logger_settings(level=log_level))
    kwargs = {
        'bind_address': f'tcp://{advertise_host}:{port}',
        'database': database,
        'curve_dir': curve_dir,
        'use_zap_auth': zap,
        'use_encryption': curvezmq,
        'server_curve_id': key_id
    }
    LOG.info('Args %s' % pformat(kwargs))
    server = SQLiteServer(**kwargs)
    try:
        server.start()
    except KeyboardInterrupt:
        LOG.warning("Keyboard Interrupt")
        server.stop()
    except Exception:
        LOG.exception("Exception in Server Thread")
        server.stop()
        raise









