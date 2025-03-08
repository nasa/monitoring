# Validate operational intent state not changed test step fragment

This step verifies that a previous action did not result in a operational intent being changed in the DSS.
It does so by querying the DSS for operational intents in the area of the flight before and after an attempted creation.
This assumes an area lock on the extent of the flight intent.

See `OpIntentValidator.expect_no_state_change()` in [test_steps.py](test_steps.py).

## 🛑 DSS responses check

If the DSS fails to reply to a query concerning operational intent references in a given area,
it is in violation of **[astm.f3548.v21.DSS0005,2](../../../requirements/astm/f3548/v21.md)**, and this check will fail.

## 🛑 Operational intent state not changed check
If operational intent reference changes, this check will fail per
**[interuss.automated_testing.flight_planning.ExpectedBehavior](../../../requirements/interuss/automated_testing/flight_planning.md)**.
