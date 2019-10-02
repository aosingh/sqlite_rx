import logging
from colorlog import ColoredFormatter


def setup_logger(name, level=logging.DEBUG):
    """Return a logger with a default ColoredFormatter."""
    formatter = ColoredFormatter(
        "%(bold_black)s%(asctime)s - %(log_color)s%(levelname)-8s%(reset)s %(blue)s%(message)s",
        datefmt=None,
        reset=True,
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red',
        }
    )

    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level=level)
    return logger
