from typing import Callable
import copy
from uas_standards.interuss.automated_testing.flight_planning.v1.api import (
    PostFlightPositionRequest,
)
from uas_standards.astm.f3548.v21.api import OperationalIntentState

from . import (v4c, p4d, gfr, lf, rfl, fr, inject,
               PositionReportError as pre,
               NoFlightPlanExistsError as nfpe, notify_user
               )

from monitoring.monitorlib.clients.flight_planning.planning import (
    PlanningActivityResult,
)
from monitoring.mock_uss.flights.database import db, PositionRecord


def check_position_conformance(
    req: PostFlightPositionRequest, flight_plan_id: str, log: Callable[[str], None]
) -> bool:
    existing_record = gfr(flight_plan_id, log)
    if existing_record:
        if "cm_on" in existing_record and existing_record.cm_on:
            # ToDo - Check if we need to lock
            with db as tx:
                tx.flight_position[flight_plan_id] = PositionRecord(
                    position_report=req.position_report,
                    position_report_id=req.position_report_id,
                )
            existing_op_intent = existing_record.op_intent
            v2 = v4c.from_interuss_scd_api(
                existing_op_intent.details.volumes
            )
            pt_in_vcol = v2.contains_pt(
                p4d.from_interuss_position_report(req.position_report)
            )
            if (
                existing_record.op_intent.reference.state
                == OperationalIntentState.Accepted
            ):
                # CM is on and Op in Accepted state, activate the flight
                try:
                    lf(flight_plan_id, log)
                    op_intent = copy.deepcopy(existing_op_intent)
                    op_intent.reference.state = OperationalIntentState.Activated
                    new_record = fr(
                        flight_info=existing_record.flight_info,
                        op_intent=op_intent,
                        mod_op_sharing_behavior=existing_record.mod_op_sharing_behavior,
                        cm_on=existing_record.cm_on,
                    )

                    response = inject(
                        flight_plan_id, new_record, existing_record, True
                    )
                    if response.activity_result == PlanningActivityResult.Completed:
                        notify_user(
                            flight_plan_id,
                            f"Successfully transitioned to {op_intent.reference.state} "
                            f"on position id {req.position_report_id}",
                        )
                    elif response.activity_result == PlanningActivityResult.Rejected:
                        # ToDo - check the correct behavior
                        # Figure out what happens when activation fails on first position
                        # Should we stop accept the future positions, as subsequent positions would fail to
                        # Or change to nonconforming state. Even though conforming in vol4d but not UTM state
                        notify_user(
                            flight_plan_id,
                            f"Transition rejected to {op_intent.reference.state} "
                            f"on position id {req.position_report_id} for reasons {response.notes}",
                        )
                        op_intent.reference.state = OperationalIntentState.Activated
                        new_record = fr(
                            flight_info=existing_record.info,
                            op_intent=op_intent,
                            mod_op_sharing_behavior=existing_record.mod_op_sharing_behavior,
                            cm_on=existing_record.cm_on,
                        )
                        res_nc = inject(
                            flight_plan_id, new_record, existing_record, True
                        )
                        if res_nc.activity_result == PlanningActivityResult.Completed:
                            notify_user(
                                flight_plan_id,
                                f"Transitioned the flight to {op_intent.reference.state} "
                                "after failed activation",
                            )
                        else:
                            notify_user(
                                flight_plan_id,
                                f"Failed transitioning to a UTM state - {response.notes}",
                            )
                    else:
                        notify_user(
                            flight_plan_id,
                            f"Failed transitioning to a UTM state - {response.notes}",
                        )
                        # Notify user of response of transitioning to new state of the flight
                finally:
                    rfl(flight_plan_id, log)
                return pt_in_vcol
        else:
            raise pre(
                "Conformance monitoring is not on for flight {flight_plan_id}. Please check if commencement of "
                "flight was notified."
            )
    else:
        raise nfpe(
            "No record exist for flight plan {flight_plan_id}. "
            "Check if the flight plan was created, or if the flight has ended."
        )


