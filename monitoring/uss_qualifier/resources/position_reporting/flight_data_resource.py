from typing import Dict

from implicitdict import ImplicitDict

from monitoring.monitorlib.clients.position_reporter.position_report_plan_interface import PositionReportsPlan

from monitoring.uss_qualifier.resources.files import load_dict
from monitoring.uss_qualifier.resources.resource import Resource
from monitoring.uss_qualifier.resources.position_reporting.flight_data import (
    FlightDataCollection,
    FlightDataSpecification,
    FlightIntentID,
)


class FlightDataResource(Resource[FlightDataSpecification]):
    _flight_data_collection: FlightDataCollection

    def __init__(self, specification: FlightDataSpecification, resource_origin: str):
        super(FlightDataResource, self).__init__(specification, resource_origin)
        has_file = "file" in specification and specification.file
        has_literal = (
            "flight_data_collection" in specification and specification.flight_data_collection
        )
        if has_file and has_literal:
            raise ValueError(
                "Only one of `file` or `flight_data_collection` may be specified in FlightDataSpecification"
            )
        if not has_file and not has_literal:
            raise ValueError(
                "One of `file` or `flight_data_collection` must be specified in FlightDataSpecification"
            )
        if has_file:
            self._flight_data_collection = ImplicitDict.parse(
                load_dict(specification.file), FlightDataCollection
            )
        elif has_literal:
            self._flight_data_collection = specification.flight_data_collection
        if "transformations" in specification and specification.transformations:
            if (
                "transformations" in self._flight_data_collection
                and self._flight_data_collection.transformations
            ):
                self._flight_data_collection.transformations.extend(
                    specification.transformations
                )
            else:
                self._flight_data_collection.transformations = specification.transformations

    def get_flight_data(self) -> Dict[FlightIntentID, PositionReportsPlan]:
        return self._flight_data_collection.resolve()
