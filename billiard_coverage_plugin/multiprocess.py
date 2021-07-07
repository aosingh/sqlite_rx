import billiard
import billiard.process
import os
import sys

from coverage.misc import contract

# An attribute that will be set on the module to indicate that it has been
# monkey-patched.
PATCHED_MARKER = "_coverage$patched"

# The environment variable that specifies the rcfile for subprocesses.
COVERAGE_RCFILE_ENV = "_COVERAGE_RCFILE"


if sys.version_info >= (3, 4):
    OriginalProcess = billiard.process.BaseProcess
else:
    OriginalProcess = billiard.Process

original_bootstrap = OriginalProcess._bootstrap

class ProcessWithCoverage(OriginalProcess):
    """A replacement for multiprocess.Process that starts coverage."""

    def _bootstrap(self):
        """Wrapper around _bootstrap to start coverage."""
        from coverage import Coverage       # avoid circular import
        rcfile = os.environ[COVERAGE_RCFILE_ENV]
        cov = Coverage(data_suffix=True, config_file=rcfile)
        cov.start()
        debug = cov.debug
        try:
            if debug.should("multiproc"):
                debug.write("Calling billiard bootstrap")
            return original_bootstrap(self)
        finally:
            if debug.should("multiproc"):
                debug.write("Finished billiard bootstrap")
            cov.stop()
            cov.save()
            if debug.should("multiproc"):
                debug.write("Saved billiard data")

class Stowaway(object):
    """An object to pickle, so when it is unpickled, it can apply the monkey-patch."""
    def __init__(self, rcfile):
        self.rcfile = rcfile

    def __getstate__(self):
        return {'rcfile': self.rcfile}

    def __setstate__(self, state):
        patch_billiard(state['rcfile'])


@contract(rcfile=str)
def patch_billiard(rcfile):
    """Monkey-patch the billiard module.
    This enables coverage measurement of processes started by billiard.
    This involves aggressive monkey-patching.
    `rcfile` is the path to the rcfile being used.
    """

    if hasattr(billiard, PATCHED_MARKER):
        return

    if sys.version_info >= (3, 4):
        OriginalProcess._bootstrap = ProcessWithCoverage._bootstrap
    else:
        billiard.Process = ProcessWithCoverage

    # Set the value in ProcessWithCoverage that will be pickled into the child
    # process.
    os.environ[COVERAGE_RCFILE_ENV] = rcfile

    # When spawning processes rather than forking them, we have no state in the
    # new process.  We sneak in there with a Stowaway: we stuff one of our own
    # objects into the data that gets pickled and sent to the sub-process. When
    # the Stowaway is unpickled, it's __setstate__ method is called, which
    # re-applies the monkey-patch.
    # Windows only spawns, so this is needed to keep Windows working.
    try:
        from billiard import spawn
        original_get_preparation_data = spawn.get_preparation_data
    except (ImportError, AttributeError):
        pass
    else:
        def get_preparation_data_with_stowaway(name):
            """Get the original preparation data, and also insert our stowaway."""
            d = original_get_preparation_data(name)
            d['stowaway'] = Stowaway(rcfile)
            return d

        spawn.get_preparation_data = get_preparation_data_with_stowaway

    setattr(billiard, PATCHED_MARKER, True)