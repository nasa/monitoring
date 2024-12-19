from implicitdict import ImplicitDict, StringBasedDateTime
from typing import List, Optional


class PositionReport(ImplicitDict):
    longitude: float
    latitude: float
    altitude: float
    time_measured: StringBasedDateTime
    speed: float
    track: float


class PositionReportPlan(ImplicitDict):
    longitude: float
    latitude: float
    altitude: float
    offset_ms: int
    speed: float
    track: float


class PositionReportsPlan(ImplicitDict):
    id: Optional[str]
    pos_url: str
    positions: List[PositionReportPlan]
