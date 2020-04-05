__version__ = "0.9.97"
__author__ = "Abhishek Singh"
__authoremail__ = "aosingh@asu.edu"


def get_default_logger_settings(level: str = "DEBUG"):

    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                '()': 'logging.Formatter',
                'format': '%(asctime)s - %(levelname)s - [%(name)s:%(funcName)s:%(lineno)d] %(message)s'
            },
        },
        'handlers': {
            'default': {
                'level': level,
                'formatter': 'standard',
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',  # Default is stderr
            },
        },
        'loggers': {
            '': {  # root logger
                'handlers': ['default'],
                'level': level,
                'propagate': False
            },
            'sqlite_rx': {
                'handlers': ['default'],
                'level': level,
                'propagate': False
            },
            '__main__': {  # if __name__ == '__main__'
                'handlers': ['default'],
                'level': level,
                'propagate': False
            },
        }
    }