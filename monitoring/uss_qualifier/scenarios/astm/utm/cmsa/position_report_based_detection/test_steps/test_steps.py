from typing import Optional, List, Tuple
import datetime
from implicitdict import ImplicitDict, StringBasedDateTime

from monitoring.uss_qualifier.scenarios.scenario import TestScenarioType
from monitoring.uss_qualifier.resources.position_reporting.position_reporter.client import PositionReporterClient
from monitoring.monitorlib.clients.position_reporter.position_report_plan_interface import (
    PositionReportsPlan, PostPositionReportsPlanRequest, PostPositionReportsPlanResponse,
    PositionReportLogsResponse, Time)
from monitoring.monitorlib.fetch import Query, QueryError


def plan_to_req(plan: PositionReportsPlan, url: str, dest_part_id: str,
                base_time: Optional[Time]) -> PostPositionReportsPlanRequest:
    return PostPositionReportsPlanRequest(
        id=dest_part_id,
        pos_url=url,
        positions=plan.position_reports,
    )


def post_position_report_plan(
    scenario: TestScenarioType,
    client: PositionReporterClient,
    plan: PositionReportsPlan,
    flight_id: str,
    pos_base_url: str,
    dest_participant_id,
    base_time: Optional[Time] = None
) -> StringBasedDateTime:
    plan_req = plan_to_req(plan, pos_base_url + f"flight_position_report/{flight_id}", dest_participant_id, base_time)
    with scenario.check(
        "Position Report plan successfully posted to PositionReporter"
    ) as check:
        try:
            t1, query = client.post_position_report_plan(flight_id, plan_req)
            scenario.record_query(query)
        except QueryError as e:
            scenario.record_queries(e.queries)
            check.record_failed(
                summary=f"Error from position reporter when posting position report plan for flight_id {flight_id}",
                details=f"{str(e)}\n\nStack trace:\n{e.stacktrace}",
                query_timestamps=[q.request.timestamp for q in e.queries],
            )
    return t1.value


def check_position_reports_posted_successfully(
    scenario: TestScenarioType,
    client: PositionReporterClient,
    flight_id: str,
    order: Optional[int]
):
    with scenario.check(
        "Position report was successfully submitted to the tested_uss"
    ) as check:
        logs, qt = get_position_report_logs(
            scenario,
            client,
            flight_id,
            order
        )
        if not logs:
            check.record_failed(
                summary=f"No log was retrieved from the position reporter for flight_id {flight_id}",
                query_timestamps=[qt],
            )
        else:
            if order and order >= 0:
                if logs[0].response.status_code != 200:
                    check.record_failed(
                        summary=f"Position report at the order {order} was not successfully submitted to tested_uss",
                        details=f"Request {logs[0].request} to post the position at order {order} gave response "
                                f"{logs[0].repsonse}",
                        query_timestamps=[logs[0].request.timestamp],
                    )
            else:
                i = 0
                for log in logs:
                    if log.response.status_code != 200:
                        check.record_failed(
                            summary=f"Position report at the order {i} was not successfully submitted to tested_uss",
                            details=f"Request {logs[0].request} to post the position at order {i} gave response "
                                    f"{logs[0].response}",
                            query_timestamps=[logs[0].request.timestamp],
                        )
                    i += 1


def get_position_report_logs(
    scenario: TestScenarioType,
    client: PositionReporterClient,
    flight_id: str,
    order: Optional[int] = -1
) -> Tuple[List[Query], datetime]:
    query = client.get_position_report_logs(flight_id, order)
    scenario.record_query(query)
    logs_res: PositionReportLogsResponse = ImplicitDict.parse(query.response.json, PositionReportLogsResponse)
    logs = logs_res.position_report_logs
    return logs, query.request.timestamp
