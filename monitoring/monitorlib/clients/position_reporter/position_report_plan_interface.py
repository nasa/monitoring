"""Data types and operations from Position Report Plan Interface 0.4.4 OpenAPI"""


from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from uas_standards import Operation

from implicitdict import ImplicitDict, StringBasedDateTime
from monitoring.monitorlib.fetch import Query

API_VERSION = "0.1.0"
"""Version of Position Report Plan Interface OpenAPI specification from which the objects in this package were generated."""

FlightPlanID = str
"""String identifying a user flight plan.  Format matches a version-4 UUID according to RFC 4122."""


class StatusResponseStatus(str, Enum):
    """The status of this automated testing interface.
    - `Starting`: the interface is starting and the automated test driver should wait before sending requests.
    - `Ready`: the interface is ready to receive test requests.
    """

    Starting = "Starting"
    Ready = "Ready"


class StatusResponse(ImplicitDict):
    status: StatusResponseStatus
    """The status of this automated testing interface.
    - `Starting`: the interface is starting and the automated test driver should wait before sending requests.
    - `Ready`: the interface is ready to receive test requests.
    """

    api_name: Optional[str]
    """Indication of the API implemented at this URL.  Must be "Position Report Plan Interface"."""

    api_version: Optional[str]
    """Indication of the API version implemented at this URL.  Must be "v0.4.4" when implementing this version of the API."""


class PositionReportPlanTransition(str, Enum):
    """Marks the first position, in a series of position reports, that causes a flight to transition to conforming or nonconforming"""

    Conforming = "Conforming"
    NonConforming = "NonConforming"


class PositionReportPlan(ImplicitDict):
    """Position report plan ."""

    latitude: float

    longitude: float

    altitude: float

    offset_ms: int
    """Time offset, in milliseconds, from the previous position. For the first position, its the offset from the
    base_time."""

    speed: float

    track: float

    transition: Optional[PositionReportPlanTransition] = None
    """Marks the first position, in a series of position reports, that causes a flight to transition to conforming or nonconforming"""


class TimeFormat(str, Enum):
    RFC3339 = "RFC3339"


class Time(ImplicitDict):
    value: StringBasedDateTime
    """RFC3339-formatted time/date string.  The time zone must be 'Z'."""

    format: TimeFormat = TimeFormat.RFC3339


class PositionReportsPlan(ImplicitDict):
    position_reports: List[PositionReportPlan]


class PostPositionReportsPlanRequest(ImplicitDict):
    """Post the flight position plan to the client"""

    id: str
    """participant id of the USS to which the position reports are to be sent."""

    pos_url: str
    """The url to which position reports have to be sent"""

    positions: List[PositionReportPlan]

    base_time: Optional[Time]
    """The time that is used for calculating the time of the positions as per the offsets in the plan. If this field is not provided, then mock_uss uses the current time as the base time."""


class PostPositionReportsPlanResponse(ImplicitDict):
    """Successful posting response contains the base_time that was used to generate the positions."""

    base_time: Optional[Time]
    """Time used as the base time for the position reports plan."""


class OperationID(str, Enum):
    GetStatus = "GetStatus"
    PostPositionReportsPlan = "PostPositionReportsPlan"
    GetPositionReportLogs = "GetPositionReportLogs"


class PositionReportLogsResponse(ImplicitDict):
    position_report_logs: List[Query]


OPERATIONS: Dict[OperationID, Operation] = {
    OperationID.GetStatus: Operation(
        id="GetStatus",
        path="/status",
        verb="GET",
        request_body_type=None,
        response_body_type={
            200: StatusResponse,
            401: None,
            403: None,
            404: None,
        },
    ),
    OperationID.PostPositionReportsPlan: Operation(
        id="PostPositionReportsPlan",
        path="/position_report_plan/{flight_plan_id}",
        verb="POST",
        request_body_type=PostPositionReportsPlanRequest,
        response_body_type={
            200: PostPositionReportsPlanResponse,
            401: None,
            403: None,
            409: None,
        },
    ),
    OperationID.GetPositionReportLogs: Operation(
        id="GetPositionReportLogs",
        path="/position_report_logs/{flight_id}",
        verb="GET",
        request_body_type=None,
        response_body_type={
            200: PositionReportLogsResponse,
            401: None,
            403: None,
            404: None,
        },
    ),
}
