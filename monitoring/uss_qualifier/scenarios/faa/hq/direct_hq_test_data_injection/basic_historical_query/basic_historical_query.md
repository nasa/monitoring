# Basic historical query test scenario

This scenario injects a standard historical operational intent corpus into a USS Historical Query
service via the test data injection API, then exercises every Historical Query endpoint and
validates that the service returns the expected data.

## Resources

### test_data

[`HQTestDataResource`](../../../../../../resources/hq/test_data.py) pointing to a corpus scenario
directory (e.g. `monitoring/uss_qualifier/test_data/hq/scenarios/basic_100`). The resource loads
all operational intent records at startup and produces the ZIP archive uploaded during injection.

### test_data_injector

[`HQTestDataInjectorResource`](../../../../../../resources/hq/test_data_injector.py) representing
the USS test data injection endpoint (defined in `interfaces/hq/test_injection.yaml`). Requires an
auth adapter authorised for scope `utm.historical_query_test_data`.

### hq_client

[`HQServiceResource`](../../../../../../resources/hq/hq_client.py) representing the USS Historical
Query service endpoint (defined in `interfaces/hq/HistoricalQueryAPISpec_v0_4.yaml`). Requires an
auth adapter authorised for scope `utm.historical_query`.

## Inject test data test case

Upload the test corpus to the service under test so subsequent query steps have data to retrieve.

### Bulk upload corpus test step

Pack the corpus directory into a ZIP archive and POST it to `POST /test_data/bulk_upload`.

#### 🛑 Successful bulk upload check

If the bulk upload endpoint does not return HTTP 201, the service under test does not correctly
implement **[automated_testing.hq.test_data_injection]**.

## Query historical data test case

Exercise every Historical Query read endpoint using the first operational intent from the injected
corpus as the focal subject.

### Query by area and time test step

Construct a `HistoricalQueryRequest` whose `area_of_interest` covers the spatial and temporal
extent of the first injected operational intent and POST it to `POST /query_operational_intents`.

#### 🛑 Successful query response check

If `POST /query_operational_intents` does not return HTTP 200, the service under test does not
correctly implement **[faa.hq.HQ0010]**.

#### 🛑 Expected operational intent returned check

If the response does not contain the operational intent ID that was injected and whose
area/time was used to construct the query, the service under test does not correctly implement
**[faa.hq.HQ0010]**.

### Retrieve operational intent versions test step

Call `GET /operational_intent/{operational_intent_id}/versions` for the focal operational intent.

#### 🛑 Successful versions response check

If `GET /operational_intent/{id}/versions` does not return HTTP 200, the service under test does
not correctly implement **[faa.hq.HQ0030]**.

#### 🛑 Expected versions returned check

If the response does not include all version numbers that were present in the injected corpus for
the focal operational intent, the service under test does not correctly implement
**[faa.hq.HQ0030]**.

### Retrieve operational intent version details test step

Call `GET /operational_intent/{operational_intent_id}/{version}` for the first version of the
focal operational intent.

#### 🛑 Successful version details response check

If `GET /operational_intent/{id}/{version}` does not return HTTP 200, the service under test does
not correctly implement **[faa.hq.HQ0020]**.

### Retrieve data exchanges test step

Call `GET /operational_intent/{operational_intent_id}/data_exchanges` for the focal operational
intent.

#### 🛑 Successful data exchanges response check

If `GET /operational_intent/{id}/data_exchanges` does not return HTTP 200, the service under test
does not correctly implement **[faa.hq.HQ0040]**.

### Retrieve operator interactions test step

Call `GET /operational_intent/{operational_intent_id}/operator_interactions` for the focal
operational intent.

#### 🛑 Successful operator interactions response check

If `GET /operational_intent/{id}/operator_interactions` does not return HTTP 200, the service
under test does not correctly implement **[faa.hq.HQ0050]**.

### Retrieve telemetry test step

Call `GET /operational_intent/{operational_intent_id}/telemetry` for the focal operational intent.

#### 🛑 Successful telemetry response check

If `GET /operational_intent/{id}/telemetry` does not return HTTP 200, the service under test does
not correctly implement **[faa.hq.HQ0060]**.

## Cleanup

The cleanup phase removes all injected test data from the service under test, regardless of
whether the scenario completed successfully.

### 🛑 Successful bulk delete check

If `DELETE /test_data/bulk_delete` does not return HTTP 200, the service under test does not
correctly implement **[automated_testing.hq.test_data_injection]**.

