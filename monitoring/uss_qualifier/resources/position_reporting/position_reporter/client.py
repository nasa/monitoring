from typing import Optional, List, Tuple

from implicitdict import StringBasedDateTime, ImplicitDict
from monitoring.monitorlib.infrastructure import AuthAdapter, UTMClientSession
from monitoring.monitorlib.fetch import query_and_describe, QueryType, Query, QueryError
from monitoring.monitorlib.clients.position_reporter.position_report_plan_interface import (
    OPERATIONS,
    OperationID,
    PostPositionReportsPlanRequest,
    PostPositionReportsPlanResponse,
    Time,
)
from monitoring.monitorlib.clients.position_reporter.scopes import (
    SCOPE_POSITION_REPORTS_PLAN,
    SCOPE_POSITION_REPORTER_STATUS,
)
from monitoring.uss_qualifier.resources.resource import Resource
from monitoring.uss_qualifier.resources.communications import AuthAdapterResource
from monitoring.uss_qualifier.reports.report import ParticipantID


class PositionReporterClient:
    def __init__(
        self,
        participant_id: str,
        reporter_base_url: str,
        auth_adapter: AuthAdapter,
        timeout_seconds: Optional[float] = None,
    ):
        self.base_url = reporter_base_url
        self.session = UTMClientSession(
            reporter_base_url, auth_adapter, timeout_seconds
        )
        self.participant_id = participant_id

    def post_position_report_plan(
        self, flight_id: str, position_reports_plan: PostPositionReportsPlanRequest
    ) -> tuple[Time | None, Query]:
        op = OPERATIONS[OperationID.PostPositionReportsPlan]
        query = query_and_describe(
            self.session,
            op.verb,
            op.path.format(flight_plan_id=flight_id),
            QueryType.InterUSSPositionReporterPlan,
            scope=SCOPE_POSITION_REPORTS_PLAN,
            json=position_reports_plan,
        )
        if query.status_code != 200:
            raise QueryError(
                f"Request to position reporter {self.base_url + op.path.format(flight_plan_id=flight_id)} "
                f"returned a {query.status_code} ",
                [query],
            )
        try:
            response: PostPositionReportsPlanResponse = ImplicitDict.parse(
                query.response.get("json"), PostPositionReportsPlanResponse
            )
        except KeyError:
            raise QueryError(
                msg=f"PostPositionReportsPlanResponse from position_reporter did not contain JSON body",
                queries=[query],
            )
        except ValueError as e:
            raise QueryError(
                msg=f"PostPositionReportsPlanResponse from mock_uss response contained invalid JSON: {str(e)}",
                queries=[query],
            )

        return response.base_time, query

    def get_position_report_logs(
        self,
        flight_id: str,
        order: Optional[int] = 0,
    ) -> Query:
        op = OPERATIONS[OperationID.GetPositionReportLogs]
        suf = f"?order={order}" if order > 0 else ""
        query = query_and_describe(
            self.session,
            op.verb,
            op.path.format(flight_id=flight_id) + suf,
            QueryType.InterUSSPositionReporterLogs,
            scope=SCOPE_POSITION_REPORTS_PLAN,
        )
        return query


class PositionReporterSpecification(ImplicitDict):
    pos_base_url: str
    participant_id: ParticipantID
    timeout_seconds: Optional[float] = None


class PositionReporterResource(Resource[PositionReporterSpecification]):
    position_reporter: PositionReporterClient

    def __init__(
        self,
        specification: PositionReporterSpecification,
        resource_origin: str,
        auth_adapter: AuthAdapterResource,
    ):
        super(PositionReporterResource, self).__init__(specification, resource_origin)
        self.position_reporter = PositionReporterClient(
            specification.participant_id,
            specification.pos_base_url,
            auth_adapter.adapter,
            specification.timeout_seconds,
        )
