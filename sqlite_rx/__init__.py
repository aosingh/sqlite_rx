__version__ = "0.9.94"
__author__ = "Abhishek Singh"
__authoremail__ = "aosingh@asu.edu"


DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            '()': 'colorlog.ColoredFormatter',
            'format': '%(bold_black)s%(asctime)s - %(log_color)s%(levelname)-8s %(bold_black)s%(filename)s:%(lineno)s %(reset)s %(blue)s%(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
        'sqlite_rx': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
        '__main__': {  # if __name__ == '__main__'
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}
