from typing import Tuple
from monitoring.monitorlib.clients.flight_planning.flight_info import (
    FlightInfo,
    AirspaceUsageState,
    UasState,
)
from monitoring.mock_uss.flights.database import FlightRecord
from uas_standards.astm.f3548.v21 import api as f3548_v21
from uas_standards.interuss.automated_testing.flight_planning.v1.api import (
    UpsertFlightPlanRequest,
)
from monitoring.mock_uss.f3548v21.flight_planning import PlanningError


def adjust_state_for_cmsa(
    new_flight_info: FlightInfo,
    op_intent: f3548_v21.OperationalIntent,
    old_record: FlightRecord,
) -> Tuple[f3548_v21.OperationalIntent, bool]:
    """
    This function adjusts the op_intent state back to existing op_intent state when mock USS provides cmsa service
    and receives a request with InUse and Nominal states.
    If old record had op_intent state as Accepted, then this request came as flight commencement trigger.

    Returns:
        - op_intent with adjusted state
        - flight_commenced_trigger
    """
    flight_commenced_trigger = False
    basic_info = new_flight_info.basic_information

    validate_flight_plan_for_cmsa(new_flight_info, old_record)

    if (
        "operator_detected_nonconformance" in new_flight_info.astm_f3548_21
        and new_flight_info.astm_f3548_21.operator_detected_nonconformance
    ):
        return op_intent, flight_commenced_trigger

    # Position
    if (
        basic_info.usage_state == AirspaceUsageState.InUse
        and basic_info.uas_state == UasState.Nominal
    ):
        op_intent.reference.state = old_record.op_intent.reference.state

    if (
        old_record
        and old_record.op_intent.reference.state
        == f3548_v21.OperationalIntentState.Accepted
    ):
        flight_commenced_trigger = True

    return op_intent, flight_commenced_trigger


def validate_flight_plan_for_cmsa(flight_info: FlightInfo, old_record: FlightRecord):
    if old_record is None:
        if (
            "position_report_details" not in flight_info.astm_f3548_21
            or flight_info.astm_f3548_21.position_report_details is None
        ) and (
            "operator_detected_nonconformance" not in flight_info.astm_f3548_21
            or flight_info.astm_f3548_21.operator_detected_nonconformance is False
        ):
            raise PlanningError(
                "First flight plan request must include position reporting details or use operator detected conformance"
            )
