# Send commencement of flight notification to start conformance monitoring test step fragment
This page describes the content of a common test step where a user sends a commencement of flight notification to the USS for a flight that is using position reporting in order to announce that the flight is about to begin. This allows the USS to initiate conformance monitoring and begin expecting position updates.

## 🛑 Successful starting of conformance monitoring check
Tested_uss should have started the conformance monitoring for flight and would indicate it by returning flight_plan_status as OkToFly
As per **[astm.f3548.v21.CMSA0010](../../../../../../requirements/astm/f3548/v21.md)** the USS starts conformance monitoring for
the flight on getting notification of commencement of flight

## 🛑 Failure check
All flight intent data provided was complete and correct. It should have been processed successfully, allowing the USS to expect the flight. If the USS returns any error indicating a failure, this check will fail per interuss.automated_testing.flight_planning.ExpectedBehavior.
