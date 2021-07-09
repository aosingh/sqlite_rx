import logging.config
import multiprocessing
import threading
import sqlite3
from typing import Any

LOG = logging.getLogger(__name__)


class SQLiteBackUp:

    def __init__(self, src, target, pages=-1) -> None:
        self.src = src
        self.target = target
        self.pages = pages
    
    
    def __call__(self, *args: Any, **kwds: Any) -> Any:

        def progress(status, remaining, total):
            copied = total - remaining
            LOG.info('Copied %s of %s pages', copied, total)

        source = sqlite3.connect(self.src)
        backup = sqlite3.connect(self.target)

        with backup:
            source.backup(backup, pages=self.pages, progress=progress)

        LOG.info("Finished Backup: Source %s , Target %s ", self.src, self.target)


class RecurringTimer(threading.Timer):

    def run(self) -> None:
        while not self.finished.wait(self.interval):
            self.function(*self.args, **self.kwargs)
