import asyncio
import uuid

import aiohttp

# import aiofiles
import logging
import datetime
import time
import json
import os

from implicitdict import StringBasedDateTime
from monitoring.position_reporter.position_reports.position_report import (
    PositionReportPlan,
    PositionReportsPlan,
)
from uas_standards.interuss.automated_testing.flight_planning.v1.api import (
    PositionReport,
    Position,
    Time,
    Velocity,
    PostFlightPositionRequest,
    Altitude,
    AltitudeReference,
    AltitudeUnits,
)
from uas_standards.interuss.automated_testing.flight_planning.v1.constants import Scope
from monitoring.monitorlib.infrastructure import AuthAdapter
from monitoring.monitorlib.fetch import (
    Query,
    QueryType,
    RequestDescription,
    ResponseDescription,
)
from monitoring.position_reporter import POS_REP_LOG_DIR


def get_position_report_from_plan(
    pr: PositionReportPlan, time_measured: datetime.datetime
) -> PositionReport:
    return PositionReport(
        position=Position(
            lat=pr.latitude,
            lng=pr.longitude,
            alt=Altitude(
                value=pr.altitude,
                reference=AltitudeReference.W84,
                units=AltitudeUnits.M,
            ),
        ),
        time_measured=Time(value=StringBasedDateTime(time_measured)),
        velocity=Velocity(speed=pr.speed, track=pr.track),
    )


async def post_position(
    pos_base_url: str,
    flight_id: str,
    order: int,
    pr: PositionReport,
    client: aiohttp.ClientSession,
):
    pr_id = str(uuid.uuid4())
    pr_req = PostFlightPositionRequest(position_report=pr, position_report_id=pr_id)
    logging.info(
        f"Posted position to {pos_base_url} : \n{json.dumps(pr_req, indent=4)}"
    )
    t0 = datetime.datetime.now(datetime.UTC)
    req = RequestDescription(
        method="POST",
        url=pos_base_url,
        headers={k: v for k, v in client.headers.items()},
        json=pr_req,
        initiated_at=StringBasedDateTime(t0),
    )
    # async with client.post(url=pos_base_url, data=json.dumps(pr)) as response:
    async with client.post(url=pos_base_url, json=pr_req) as response:
        t1 = datetime.datetime.now(datetime.UTC)
        # ToDo - Catch errors
        res_text = await response.text()
        kwargs = {
            "code": response.status,
            "headers": {k: v for k, v in response.headers.items()},
            "reported": StringBasedDateTime(datetime.datetime.now(datetime.UTC)),
            "elapsed_s": (t1 - t0).total_seconds(),
        }
        if is_json(res_text):
            kwargs["json"] = json.loads(res_text)
        else:
            kwargs["body"] = res_text
        logging.info(f"Response body - {res_text}")
        q = Query(
            request=req,
            response=ResponseDescription(**kwargs),
            query_type=QueryType.InterUSSPositionReportSubmit,
        )
        log_file(flight_id, order, q)

        logging.info(f"Response status received: {response.status}")
        logging.debug(f"Response received: {res_text}")


def is_json(json_text):
    try:
        json.loads(json_text)
    except ValueError as e:
        return False
    return True


async def send_positions_periodically(
    flight_id: str,
    pos_url: str,
    prs: PositionReportsPlan,
    client: aiohttp.ClientSession,
    time_start: datetime.datetime,
):
    tasks = []
    prev_time = time_start
    i = -1
    for pr in prs.positions:
        i += 1
        next_time = prev_time + datetime.timedelta(seconds=pr.offset_ms / 1000)
        prev_time = next_time
        position_report = get_position_report_from_plan(pr, next_time)
        logging.info(f"\n Position {i} - {position_report}\n")
        await asyncio.sleep(pr.offset_ms / 1000)
        task = asyncio.create_task(
            post_position(pos_url, flight_id, i, position_report, client)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks)


async def send_position_reports_async(
    req_id: str,
    flight_id: str,
    auth_client: AuthAdapter,
    prs: PositionReportsPlan,
    time_start: datetime.datetime,
):
    # pos_url = f"{prs.pos_url}/{flight_id}"
    pos_url = prs.pos_url
    auth_token = auth_client.get_headers(url=pos_url, scopes=[Scope.PositionReport])
    async with aiohttp.ClientSession(headers=auth_token) as client:
        task2 = asyncio.create_task(
            send_positions_periodically(flight_id, pos_url, prs, client, time_start)
        )
        await task2
        logging.info("All position reports sent")

    await client.close()
    logging.debug("Closed session")

    logging.info(f"==Req id {req_id} : Sent all position reports.")


def send_position_reports(
    req_id: str,
    flight_id: str,
    auth_client: AuthAdapter,
    prs: PositionReportsPlan,
    time_start: datetime.datetime,
):
    logging.info(f"Start req id {req_id} at {time_start}")
    wait_to_start = time_start - datetime.datetime.now(datetime.UTC)
    if wait_to_start.total_seconds() >= 0:
        time.sleep(wait_to_start.total_seconds())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        send_position_reports_async(req_id, flight_id, auth_client, prs, time_start)
    )

    logging.info(
        f"Completed position reports for {flight_id} to {prs.pos_url} at {datetime.datetime.now(datetime.UTC)}"
    )


def log_file(flight_id: str, order: int, content: Query) -> None:
    log_path = POS_REP_LOG_DIR
    n = len(os.listdir(log_path))
    basename = f"{flight_id}_{order}.json"

    with open(os.path.join(log_path, basename), "w") as f:
        logging.info(f"Writing to file {basename} started at {datetime.datetime.now()}")
        f.write(json.dumps(content))
        logging.info(f"Writing to file {basename} ended at {datetime.datetime.now()}")
