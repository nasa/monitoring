# Spatial conformance monitoring of positions by USS test scenario

## Description
This test checks that the USS being tested validates the operational intents received as response to its GET request from another USS.
mock_uss plans an operation designed to be relevant to (but not intersect) the operation tested_uss will plan, and provides the data that tested_uss GETs.
tested_uss validates the GET response from mock_uss and accordingly plan its operation.

The primary requirement tested by this scenario is **[astm.f3548.v21.SCD0035](../../../../../requirements/astm/f3548/v21.md)** because a USS cannot verify its operational intent does not conflict when it cannot obtain valid details for that operational intent.

This scenario assumes that the area used in the scenario is already clear of any pre-existing flights (using, for instance, PrepareFlightPlanners scenario).

## Resources
### flight_intents
FlightIntentsResource provides the two flight intents which must be relevant to each other, but must not intersect.
This can generally be accomplished when the convex hulls of the 2D footprints of the two flights intersect, but the polygons do not intersect.
There is an overlap in time and altitude of the two flights.
- flight_1
- flight_2
- flight_1_commenced

### mock_uss
MockUSSResource that will be used for planning flights, controlling data shared for validation testing, and gathering interuss interactions from mock_uss.

### tested_uss
FlightPlannerResource that will be used for the USS being tested for its data validation of operational intent.

### dss
DSSInstanceResource that provides access to a DSS instance where flight creation/sharing can be verified.

### position_reporter
PositionReporter client that submits the test position report plan.

### flight_data
Position reports plan for the test.
  - flight1_conforming

## Successfully monitor conformance with conforming positions test case

### mock_uss plans flight 2 test step

#### [Plan successfully](../../../../flight_planning/plan_flight_intent.md)

Flight 2 should be successfully planned by mock_uss.

#### [Validate operational intent is shared](../../validate_shared_operational_intent.md)

### tested_uss plans flight 1 test step

#### [Plan successfully](../../../../flight_planning/plan_flight_intent.md)

The test driver instructs tested_uss to attempt to plan flight 1. tested_uss checks if any conflicts with flight 2
which is of equal priority and came first.

#### [Validate operational intent is shared](../../validate_shared_operational_intent.md)

### [Validate tested_uss obtained flight2 details test step](../../data_exchange_validation/test_steps/validate_operational_intent_details_obtained.md)
Validate that tested_uss obtained flight2 details from mock_uss, by means of either
a notification pushed by mock_uss to tested_uss due to the pre-existing subscription, or
direct retrieval by tested_uss from mock_uss.

### [Validate flight1 Notification sent to mock_uss test step](../../data_exchange_validation/test_steps/validate_notification_operational_intent.md)
tested_uss notifies mock_uss of flight 1, due to mock_uss's subscription covering flight 2 (which is necessarily relevant to flight 1 per test design).

### Send commencement of flight1 notification to start conformance monitoring by tested_uss test step

#### [Commence flight1](./test_steps/commencement_of_flight.md)

#### [Validate operational intent not changed](../../validate_not_changed_operational_intent.md)

### Post Position report plan for flight1 to activate test step

#### [Post Position report plan](./test_steps/post_position_report_plan.md)
Submit the position reports plan to the Position Reporter. Position reporter will return the
base time for the offsets of the position report plan.

#### [Check first position for flight1 was posted successfully to tested_uss](./test_steps/check_positions_posted.md)
Verify first position is sent by Position Reporter.

#### [Validate flight1 is shared with Activated state by tested_uss](../../validate_shared_operational_intent.md)

#### Intent transitioned to Activated state check
As per **[astm.f3548.v21.CMSA0015](../../../../../requirements/astm/f3548/v21.md)** , the USS transitions the intent to Activated state

### [Validate flight1 Notification sent to mock_uss test step](../../data_exchange_validation/test_steps/validate_notification_operational_intent.md)
tested_uss notifies mock_uss of flight1 state transition to Activated state

### [End tested_uss flight test step](../../../../flight_planning/delete_flight_intent.md)
End the tested_uss's flight 1.

### [Validate flight1 Notification sent to mock_uss test step](../../data_exchange_validation/test_steps/validate_notification_operational_intent.md)
tested_uss notifies mock_uss of flight1 transition to an Ended state.

#### [Validate operational intent not shared](../../validate_not_shared_operational_intent.md)
tested_uss must no more share flight1 at its /uss/operational_intent endpoint.

### [Delete mock_uss flight test step](../../../../flight_planning/delete_flight_intent.md)
End mock_uss's flight 2, to clean up for next test case.

## Cleanup
### Successful flight deletion check
This cleanup is for both - after testcase ends and after test scenario ends
**[interuss.automated_testing.flight_planning.DeleteFlightSuccess](../../../../../requirements/interuss/automated_testing/flight_planning.md)**
