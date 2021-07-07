from coverage import CoveragePlugin, Coverage
from coverage.config import CoverageConfig
from .multiprocess import patch_billiard

class BilliardCoveragePlugin(CoveragePlugin):
    def configure(self, config):
        # coverage does not want us to do this, see
        # https://github.com/nedbat/coveragepy/blob/6ddd8c8e3abf1321277a07ecd2a5b1c857163ee1/coverage/control.py#L271-L275
        if isinstance(config, CoverageConfig):
            config_file = config.config_file
        elif isinstance(config, Coverage):
            config_file = config.config.config_file
        else:
            raise RuntimeError('Unexpected config type.')

        patch_billiard(rcfile=config_file)


def coverage_init(reg, options):
    reg.add_configurer(BilliardCoveragePlugin())