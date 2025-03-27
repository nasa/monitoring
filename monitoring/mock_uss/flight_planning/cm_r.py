import flask
import os
from loguru import logger
from typing import Optional, List, Tuple
from implicitdict import ImplicitDict

from uas_standards.interuss.automated_testing.flight_planning.v1.constants import Scope
from uas_standards.interuss.automated_testing.flight_planning.v1.api import (
    PostFlightPositionRequest,
)
from monitoring.mock_uss import webapp
from monitoring.mock_uss.auth import requires_scope
from monitoring.monitorlib.idempotency import idempotent_request
from .conformance.position_conformance_check import (
    check_position_conformance,
)
from .conformance import PositionReportError, NoFlightPlanExistsError


@webapp.route("/flight_position_report/<flight_plan_id>", methods=["POST"])
@requires_scope(Scope.PositionReport)
@idempotent_request()
def post_position_report(flight_plan_id: str) -> Tuple[str, int]:
    def log(msg: str) -> None:
        logger.debug(f"[position_report/{os.getpid()}:{flight_plan_id}] {msg}")

    req_data = flask.request.data
    log(f"Starting handler. Received {req_data}")
    try:
        json = flask.request.json
        if json is None:
            raise ValueError("Request did not contain a JSON payload")
        req_body: PostFlightPositionRequest = ImplicitDict.parse(
            json, PostFlightPositionRequest
        )
    except ValueError as e:
        log(f"**** ValueError {e}")
        msg = "Create flight {} unable to parse JSON: {}".format(flight_plan_id, e)
        return msg, 400
    logger.info(f"Received position report for {flight_plan_id} -{req_body}")
    conformance = False
    try:
        if check_position_conformance(req_body, flight_plan_id, log):
            conformance = True
    except NoFlightPlanExistsError as nfpe:
        return str(nfpe), 404
    except PositionReportError as pre:
        log(f"**** PositionReportError {pre}")
        return str(pre), 400
    except Exception as e:
        logger.error(str(e))
        return str(e), 500

    resp_msg = {"conforming": conformance}
    return flask.jsonify(resp_msg), 200
