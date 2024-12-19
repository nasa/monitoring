import flask
import os
import logging
from typing import Optional


class PositionReporter(flask.Flask):

    def __init__(self, *args, **kwargs):
        self._pid = os.getpid()
        super(PositionReporter, self).__init__(*args, **kwargs)

    def setup(self):
        logging.info(f"Position Reporter Setup from process {self._pid}")

    def start_periodic_tasks_daemon(self):
        logging.info(f"Initiating periodic task daemon from process {self._pid}")

    def shutdown(self, signal_number: Optional[int], stack):
        if os.getpid() != self._pid:
            logging.debug(f"Process {os.getpid()} skipping shutdown procedure")
            return

        logging.debug(
            f"Process {os.getpid()} stopped with signal {signal_number} while MockUSS server was not stopping"
        )

