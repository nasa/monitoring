import random

import logging
import json
import os
import uuid
import threading
import datetime
from flask import jsonify, request, Response
from typing import Tuple
from implicitdict import ImplicitDict, StringBasedDateTime

from monitoring.position_reporter import get_auth_client
from monitoring.position_reporter.position_reports.retriever import get_flight_logs
from monitoring.monitorlib.clients.position_reporter.position_report_plan_interface import (
    PostPositionReportsPlanRequest,
    PostPositionReportsPlanResponse,
    PositionReportLogsResponse,
    Time,
)
from monitoring.position_reporter.position_reports.sender import send_position_reports
from monitoring.position_reporter import webapp, POS_REP_LOG_DIR


@webapp.route("/status", methods=["GET"])
def status():
    # req = flask.request.json
    res = {
        "status": "Ready",
        "api_name": "Position Report Plan Interface",
        "api_version": "v0.1.0",
    }
    return jsonify(res), 200


@webapp.route("/position_report_plan/<flight_plan_id>", methods=["POST"])
def send_pos(flight_plan_id: str) -> Tuple[(Response | str), int]:
    # Start a new thread to send the periodic POST requests
    req_plan = request.json
    logging.debug(f"Received input json for {flight_plan_id} - {req_plan}")

    if "request_id" in req_plan:
        req_id = req_plan["request_id"]
    else:
        req_id = uuid.uuid4()

    positions_plan: PostPositionReportsPlanRequest = ImplicitDict.parse(
        json.loads(json.dumps(req_plan)), PostPositionReportsPlanRequest
    )
    # if positions_plan.base_time:
    #     return f"base_time field feature not implemented", 501

    logging.debug(f"Incoming req thread - {threading.current_thread().name}")

    time_start = datetime.datetime.now(datetime.UTC)

    logging.info(f"Time start for positions - {time_start}")

    threading.Thread(
        target=send_position_reports,
        kwargs={
            "req_id": req_id,
            "flight_id": flight_plan_id,
            "auth_client": get_auth_client(),
            "prs": positions_plan,
            "time_start": time_start,
        },
    ).start()

    logging.debug(
        f"End of req  id {req_id} main thread - {threading.current_thread().name}\n"
    )

    return (
        jsonify(
            PostPositionReportsPlanResponse(
                base_time=Time(value=StringBasedDateTime(time_start))
            )
        ),
        200,
    )


@webapp.route("/position_report_logs/<flight_id>", methods=["GET"])
def get_logs(flight_id: str) -> Tuple[Response, int]:
    order = request.args.get("order", default=-1, type=int)

    log_path = POS_REP_LOG_DIR

    if not os.path.exists(log_path):
        raise ValueError(f"Configured log path {log_path} does not exist")

    logs = get_flight_logs(flight_id, order)

    return jsonify(PositionReportLogsResponse(position_report_logs=logs)), 200


@webapp.route("/position_report_logs", methods=["DELETE"])
def delete_logs() -> Tuple[str, int]:
    log_path = POS_REP_LOG_DIR
    if not os.path.exists(log_path):
        raise ValueError(f"Configured log path {log_path} does not exist")

    logging.debug(f"Number of files in {log_path}: {len(os.listdir(log_path))}")

    num_removed = 0
    for file in os.listdir(log_path):
        file_path = os.path.join(log_path, file)
        os.remove(file_path)
        logging.debug(f"Removed log file - {file_path}")
        num_removed = num_removed + 1

    return f"Removed {num_removed} files", 200
