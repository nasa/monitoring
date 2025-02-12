import datetime
import time
import math
from typing import Optional, Dict, Set
from loguru import logger

from monitoring.monitorlib.clients.flight_planning.flight_info import (
    AirspaceUsageState,
    UasState,
)
from monitoring.monitorlib.clients.flight_planning.flight_info_template import (
    FlightInfoTemplate,
)
from monitoring.uss_qualifier.resources.position_reporting.position_reporter.client import PositionReporterClient

from monitoring.uss_qualifier.scenarios.astm.utm.data_exchange_validation.test_steps.wait import (
    MaxTimeToWaitForSubscriptionNotificationSeconds as max_wait_time,
)
from monitoring.monitorlib.delay import sleep
from monitoring.monitorlib.temporal import TimeDuringTest
import arrow
from monitoring.monitorlib.temporal import Time
from urllib.parse import urlsplit
from monitoring.monitorlib.clients.flight_planning.client import FlightPlannerClient
from monitoring.uss_qualifier.resources.astm.f3548.v21 import DSSInstanceResource
from monitoring.uss_qualifier.resources.astm.f3548.v21.dss import DSSInstance
from monitoring.uss_qualifier.resources.flight_planning import (
    FlightIntentsResource,
)
from monitoring.uss_qualifier.resources.position_reporting.flight_data_resource import FlightDataResource
from monitoring.uss_qualifier.resources.flight_planning.flight_intent_validation import (
    ExpectedFlightIntent,
    validate_flight_intent_templates,
)
from monitoring.uss_qualifier.resources.flight_planning.flight_planners import (
    FlightPlannerResource,
)

from monitoring.uss_qualifier.resources.interuss.mock_uss.client import (
    MockUSSClient,
    MockUSSResource,
)
from monitoring.uss_qualifier.resources.position_reporting.position_reporter.client import (
    PositionReporterResource
)
from monitoring.uss_qualifier.scenarios.astm.utm.test_steps import (
    OpIntentValidator,
)
from monitoring.uss_qualifier.scenarios.astm.utm.data_exchange_validation.test_steps.expected_interactions_test_steps import (
    expect_mock_uss_receives_op_intent_notification,
    expect_uss_obtained_op_intent_details,
)

from monitoring.uss_qualifier.scenarios.scenario import (
    TestScenario,
    ScenarioCannotContinueError,
)
from monitoring.uss_qualifier.scenarios.flight_planning.test_steps import (
    cleanup_flights,
    plan_flight,
    delete_flight,
    commence_monitoring
)
from monitoring.uss_qualifier.suites.suite import ExecutionContext
from uas_standards.astm.f3548.v21.api import EntityID, OperationalIntentState, OperationalIntentReference
from uas_standards.astm.f3548.v21.constants import Scope
from monitoring.monitorlib.clients.position_reporter.position_report_plan_interface import PositionReportsPlan
from monitoring.uss_qualifier.scenarios.astm.utm.cmsa.position_report_based_detection.test_steps.test_steps import (
    post_position_report_plan, check_position_reports_posted_successfully
)


class PositionReportBasedSpatialConformanceMonitoring(TestScenario):
    flight_1: FlightInfoTemplate
    flight_2: FlightInfoTemplate
    flight_1_commenced: FlightInfoTemplate

    op_intent_ids: Set[EntityID]

    tested_uss_client: FlightPlannerClient
    mock_uss: MockUSSClient
    mock_uss_client: FlightPlannerClient
    dss: DSSInstance
    position_reporter_client: PositionReporterClient

    def __init__(
        self,
        tested_uss: FlightPlannerResource,
        mock_uss: MockUSSResource,
        dss: DSSInstanceResource,
        position_reporter: PositionReporterResource,
        flight_intents: Optional[FlightIntentsResource] = None,
        flight_data: Optional[FlightDataResource] = None
    ):
        super().__init__()
        self.tested_uss_client = tested_uss.client
        self.mock_uss = mock_uss.mock_uss
        self.mock_uss_client = mock_uss.mock_uss.flight_planner
        self.dss = dss.get_instance(
            {
                Scope.StrategicCoordination: "search for operational intent references to verify outcomes of planning activities"
            }
        )
        self.position_reporter_client = position_reporter.position_reporter
        if not flight_intents:
            msg = f"No FlightIntentsResource was provided as input to this test, it is assumed that the jurisdiction does not allow any same priority conflicts, execution of the scenario was stopped without failure"
            self.record_note(
                "Jurisdiction of tested USS does not allow any same priority conflicts",
                msg,
            )
            raise ScenarioCannotContinueError(msg)
        # if not position_reports_plan
        expected_flight_intents = [
            ExpectedFlightIntent(
                "flight_1",
                "Flight 1",
                must_not_conflict_with=["Flight 2"],
                f3548v21_priority_equal_to=["Flight 2"],
                usage_state=AirspaceUsageState.Planned,
                uas_state=UasState.Nominal,
                # TODO: Must intersect bounding box of Flight 2
            ),
            ExpectedFlightIntent(
                "flight_2",
                "Flight 2",
                must_not_conflict_with=["Flight 1"],
                f3548v21_priority_equal_to=["Flight 1"],
                usage_state=AirspaceUsageState.Planned,
                uas_state=UasState.Nominal,
                # TODO: Must intersect bounding box of Flight 1
            ),
            ExpectedFlightIntent(
                "flight_1_commenced",
                name="Flight 1",
                must_not_conflict_with=["Flight 2"],
                usage_state=AirspaceUsageState.InUse,
                uas_state=UasState.Nominal,
            )
        ]

        templates = flight_intents.get_flight_intents()
        try:
            validate_flight_intent_templates(templates, expected_flight_intents)
        except ValueError as e:
            raise ValueError(
                f"`{self.me()}` TestScenario requirements for flight_intents not met: {e}"
            )

        for efi in expected_flight_intents:
            setattr(self, efi.intent_id, templates[efi.intent_id])

        # position_report_plan
        if not flight_data:
            msg = (f"No FlightDataResource was provided as input to this CMSA test scenario, flight_data is required. "
                   f"Hence execution of the scenario was stopped without failure")
            self.record_note(
                "FlightDataResource missing for CMSA tests",
                msg,
            )
            raise ScenarioCannotContinueError(msg)

        self.flight_data = flight_data.get_flight_data()

    def run(self, context: ExecutionContext):
        self.op_intent_ids = set()
        times = {
            TimeDuringTest.StartOfTestRun: Time(context.start_time),
            TimeDuringTest.StartOfScenario: Time(arrow.utcnow().datetime),
        }
        self.begin_test_scenario(context)

        self.record_note(
            "Tested USS",
            f"{self.tested_uss_client.participant_id}",
        )

        self.begin_test_case("Successfully monitor conformance with conforming positions")
        self._monitor_conformance_test_case(times)
        self.end_test_case()

        self.end_test_scenario()

    def _monitor_conformance_test_case(self, times: Dict[TimeDuringTest, Time]):
        times[TimeDuringTest.TimeOfEvaluation] = Time(arrow.utcnow().datetime)
        flight_2 = self.flight_2.resolve(times)

        self.begin_test_step("mock_uss plans flight 2")
        with OpIntentValidator(
            self,
            self.mock_uss_client,
            self.dss,
            flight_2.basic_information.area.bounding_volume.to_f3548v21(),
        ) as validator:
            flight_2_planning_time = Time(arrow.utcnow().datetime)
            _, self.flight_2_id = plan_flight(
                self,
                self.mock_uss_client,
                flight_2,
            )

            flight_2_oi_ref = validator.expect_shared(flight_2)
            self.op_intent_ids.add(flight_2_oi_ref.id)
        self.end_test_step()

        times[TimeDuringTest.TimeOfEvaluation] = Time(arrow.utcnow().datetime)
        flight_1 = self.flight_1.resolve(times)

        self.begin_test_step("tested_uss plans flight 1")
        with OpIntentValidator(
            self,
            self.tested_uss_client,
            self.dss,
            flight_1.basic_information.area.bounding_volume.to_f3548v21(),
        ) as validator:
            flight_1_planning_time = Time(arrow.utcnow().datetime)
            plan_res, self.flight_1_id = plan_flight(
                self,
                self.tested_uss_client,
                flight_1,
            )
            flight_1_oi_ref = validator.expect_shared(flight_1)
            self.op_intent_ids.add(flight_1_oi_ref.id)
        self.end_test_step()

        self.begin_test_step("Validate tested_uss obtained flight2 details")
        sleep(
            max_wait_time,
            "we have to wait the longest it may take a USS to send a notification before we can establish another USS has obtained operational intent details",
        )
        expect_uss_obtained_op_intent_details(
            self,
            self.mock_uss,
            flight_2_planning_time,
            flight_2_oi_ref.id,
            self.tested_uss_client.participant_id,
        )
        self.end_test_step()

        self.begin_test_step("Validate flight1 Notification sent to mock_uss")
        expect_mock_uss_receives_op_intent_notification(
            self,
            self.mock_uss,
            flight_1_planning_time,
            flight_1_oi_ref.id,
            self.tested_uss_client.participant_id,
            plan_res.queries[0].request.timestamp,
        )
        self.end_test_step()

        # Commencement of flight of tested_uss
        self.begin_test_step(
            "Send commencement of flight1 notification to start conformance monitoring by tested_uss")
        # BasicFlightPlanInformationUsageState=InUse
        # BasicFlightPlanInformationUasState=Nominal with no area means commencement of flight notification
        flight_1_commenced = self.flight_1_commenced.resolve(times)

        with OpIntentValidator(
            self,
            self.tested_uss_client,
            self.dss,
            flight_1.basic_information.area.bounding_volume.to_f3548v21(),
            flight_1_oi_ref,
        ) as validator:
            commence_monitoring(
                self,
                self.tested_uss_client,
                flight_1_commenced,
                self.flight_1_id,
            )
            # time.sleep(2)
            # Might need to add some wait later to check whether shared

            validator.expect_no_change()

        self.end_test_step()

        self.begin_test_step("Post Position report plan for flight1 to activate")
        flight1_data: PositionReportsPlan = self.flight_data["flight1_conforming"]
        # Post position plan to tested_uss
        with OpIntentValidator(
            self,
            self.tested_uss_client,
            self.dss,
            flight_1.basic_information.area.bounding_volume.to_f3548v21(),
            flight_1_oi_ref,
        ) as validator:
            t1 = post_position_report_plan(
                self,
                self.position_reporter_client,
                flight1_data,
                self.flight_1_id,
                "{0.scheme}://{0.netloc}/".format(urlsplit(self.tested_uss_client.get_base_url())),
                self.tested_uss_client.participant_id,
            )

            wait_time = t1.datetime + datetime.timedelta(
                milliseconds=(flight1_data.position_reports[0].offset_ms + 2000))
            logger.info(f"Returned t1 {t1.datetime} and wait time {wait_time}")
            wait_until(wait_time)

            check_position_reports_posted_successfully(
                self,
                self.position_reporter_client,
                self.flight_1_id,
                0
            )

            last_flight_info = flight_1_commenced
            # self.begin_test_step("Tested_uss shares flight1 intent transitioned to Activated state")
            flight_1_oi_ref_latest = validator.expect_shared(
                last_flight_info,
                expected_state=OperationalIntentState.Activated)
            self._check_intent_activated(flight_1_oi_ref, flight_1_oi_ref_latest, self.tested_uss_client.participant_id)
        self.end_test_step()

        time.sleep(self._time_for_all_reports(flight1_data, 1))

        self.begin_test_step("End tested_uss flight")
        delete_flight(self, self.tested_uss_client, self.flight_1_id)
        self.end_test_step()

        self.begin_test_step("Delete mock_uss flight")
        delete_flight(self, self.mock_uss_client, self.flight_2_id)
        self.end_test_step()

    def _time_for_all_reports(self, reports: PositionReportsPlan, order: int):
        """
        Returns time in seconds for all reports to be posted from order in the reports
        """
        delta = 0
        for r in reports.position_reports[order:]:
            delta += r.offset_ms
        logger.info(f"Total time for all position reports to be posted {delta} milliseconds")

        return math.ceil(delta/1000)

    def _check_intent_activated(
        self,
        oi_ref_before_transition: OperationalIntentReference,
        oi_ref_after_transition: OperationalIntentReference,
        participant_id: str
    ):
        with self.check(
            "Intent transitioned to Activated state", participant_id
        ) as check:
            if oi_ref_after_transition.state != OperationalIntentState.Activated:
                check.record_failed(
                    summary="The intent should have been in Activated state",
                    details=f"The intent should have been in Activated state, but is in {oi_ref_after_transition.state}"
                )
            else:
                if oi_ref_before_transition == OperationalIntentState.Activated:
                    check.record_failed(
                        summary="There should have been transition of intent to Activated state",
                        details="The previous state of intent was Activated as well, so no transition took place."
                    )

    def cleanup(self):
        self.begin_cleanup()
        cleanup_flights(self, (self.mock_uss_client, self.tested_uss_client)),
        self.end_cleanup()


def wait_until(t1: datetime):
    """
        t1: time till which to wait
    """
    diff = t1 - datetime.datetime.now(datetime.UTC)
    logger.info(f"diff second to sleep- {diff.total_seconds()}")
    if diff > datetime.timedelta(seconds=0):
        time.sleep(diff.total_seconds())
        logger.info(f"**** Slept for {diff.total_seconds()} seconds")
    else:
        logger.info("**** Didn't need to sleep")
