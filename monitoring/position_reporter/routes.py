import random

import logging
import json
import threading
import datetime
import flask
from implicitdict import ImplicitDict

from monitoring.position_reporter import get_auth_client
from monitoring.position_reporter.position_reports.position_report import (
    PositionReportsPlan,
)
from monitoring.position_reporter.position_reports.sender import send_position_reports
from monitoring.position_reporter import webapp


@webapp.route("/status", methods=["GET"])
def status():
    # req = flask.request.json
    res = {
        "status": "Ready",
        "api_name": "Position Report Plan Interface",
        "api_version": "v0.1.0",
    }
    return flask.jsonify(res), 200


@webapp.route("/send_pos", methods=["POST"])
def send_pos():
    # Start a new thread to send the periodic POST requests
    req_plan = flask.request.json

    req_id = random.randint(1, 100)

    positions_plan = ImplicitDict.parse(req_plan, PositionReportsPlan)

    logging.info(f"******* Incoming req thread - {threading.current_thread().name}")

    time_start = datetime.datetime.now()

    logging.info(f"Time start for positions - {time_start}")

    threading.Thread(
        target=send_position_reports,
        kwargs={
            "req_id": req_id,
            "pos_url": positions_plan.pos_url,
            "auth_client": get_auth_client(),
            "prs": positions_plan.positions,
            "time_start": time_start,
        },
    ).start()

    logging.info(
        f"******* End of req  id {req_id} main thread - {threading.current_thread().name}"
    )

    return f"Completed POST requests to {positions_plan.pos_url} at {datetime.datetime.now()}"
