from monitoring.mock_uss.flights.planning import (
    get_flight_record as gfr,
    lock_flight as lf,
    release_flight_lock as rfl,
)
from monitoring.monitorlib.geotemporal import Volume4DCollection as v4c, Point4D as p4d
from monitoring.mock_uss.flights.database import FlightRecord as fr, PositionRecord as pr
from monitoring.mock_uss.scd_injection.routes_injection import inject_flight as inject


class PositionReportError(Exception):
    pass


class NoFlightPlanExistsError(Exception):
    pass


def notify_user(flight_plan_id: str, msg: str):
    # ToDo This can be sent as a notification to user. But check if that is a req
    # Currently printing it
    print(f"Notification to user of {flight_plan_id} - {msg}")
