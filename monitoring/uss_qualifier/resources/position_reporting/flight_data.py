from typing import Optional, Dict, List
from implicitdict import ImplicitDict
import json

from monitoring.monitorlib.transformations import Transformation, RelativeTranslation
from monitoring.uss_qualifier.resources.flight_planning.flight_intent import (
    FlightIntentID,
)
from monitoring.uss_qualifier.resources.files import ExternalFile
from monitoring.monitorlib.clients.position_reporter.position_report_plan_interface import (
    PositionReportPlan,
    PositionReportsPlan,
)

FlightDataID = str
"""Identifier for a position reports plan within a collection of flight data.
To be used only within uss_qualifier (not visible to participants under test) to select an appropriate position reports plan from the collection."""


class FlightDataCollection(ImplicitDict):
    """Specification for a collection of flight intents, each identified by a FlightIntentID."""

    flight_data: Dict[FlightIntentID, PositionReportsPlan]
    """Flight planning actions that users want to perform."""

    transformations: Optional[List[Transformation]]
    """Transformations to append to all FlightInfoTemplates."""

    def resolve(self) -> Dict[FlightIntentID, PositionReportsPlan]:
        """Resolve the underlying delta flight intents."""

        # process intents in order of dependency to resolve deltas
        processed_flight_data: Dict[FlightIntentID, PositionReportsPlan] = {}
        unprocessed_intent_ids = list(self.flight_data.keys())

        while unprocessed_intent_ids:
            nb_processed = 0
            for intent_id in unprocessed_intent_ids:
                unprocessed_flight_data = self.flight_data[intent_id]
                processed_position_reports_plan: List[PositionReportPlan] = []
                if isinstance(unprocessed_flight_data, PositionReportsPlan):
                    for x in unprocessed_flight_data.position_reports:
                        processed_flight_data_template = ImplicitDict.parse(
                            json.loads(json.dumps(x)),
                            PositionReportPlan,
                        )

                        if self.transformations:
                            for transformation in self.transformations:
                                if (
                                    "relative_translation" in transformation
                                    and transformation.relative_translation
                                ):
                                    processed_position_reports_plan.append(
                                        transform(
                                            processed_flight_data_template,
                                            transformation.relative_translation,
                                        )
                                    )
                        else:
                            processed_position_reports_plan.append(
                                processed_flight_data_template
                            )
                else:
                    raise ValueError(
                        f"{intent_id} flight intent in FlightDataCollection is invalid; must specify `plan` - a list of Position reports"
                    )

                nb_processed += 1
                processed_flight_data[intent_id] = PositionReportsPlan(
                    position_reports=processed_position_reports_plan
                )
                unprocessed_intent_ids.remove(intent_id)

            if nb_processed == 0 and unprocessed_intent_ids:
                raise ValueError(
                    "Unresolvable dependency detected between intents: "
                    + ", ".join(i_id for i_id in unprocessed_intent_ids)
                )

        return processed_flight_data


def transform(
    position_report_plan_template: PositionReportPlan, translation: RelativeTranslation
) -> PositionReportPlan:
    if (
        translation.has_field_with_value("degrees_north")
        and translation.has_field_with_value("degrees_east")
        and translation.has_field_with_value("meters_up")
    ):
        lat = position_report_plan_template.latitude + translation.degrees_north
        lng = position_report_plan_template.longitude + translation.degrees_east
        alt = position_report_plan_template.altitude + translation.meters_up

        pr_plan = PositionReportPlan(
            latitude=lat,
            longitude=lng,
            altitude=alt,
            offset_ms=position_report_plan_template.offset_ms,
            speed=position_report_plan_template.speed,
            track=position_report_plan_template.track,
        )
        if position_report_plan_template.transition:
            pr_plan.transition = position_report_plan_template.transition
        return pr_plan
    else:
        raise ValueError("Provide a relative translation for the position reports.")


class FlightDataSpecification(ImplicitDict):
    """Exactly one field must be specified."""

    flight_data_collection: Optional[FlightDataCollection]
    """Full flight intent collection, or a $ref to an external file containing a FlightIntentCollection."""

    file: Optional[ExternalFile]
    """Location of file to load, containing a FlightIntentCollection"""

    transformations: Optional[List[Transformation]]
    """Transformations to apply to all flight intents' 4D volumes after resolution (if specified)"""
