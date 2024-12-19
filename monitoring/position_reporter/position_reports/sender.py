import asyncio
import aiohttp
import logging
import datetime
import time
import json

from implicitdict import StringBasedDateTime
from monitoring.position_reporter.position_reports.position_report import (
    PositionReport,
    PositionReportPlan,
    PositionReportsPlan,
)
from monitoring.monitorlib.infrastructure import AuthAdapter


def get_position_report_from_plan(
    pr: PositionReportPlan, time_measured: datetime.datetime
) -> PositionReport:
    return PositionReport(
        latitude=pr.latitude,
        longitude=pr.longitude,
        altitude=pr.latitude,
        time_measured=StringBasedDateTime(time_measured),
        speed=pr.speed,
        track=pr.track,
    )


async def post_position(
    pos_base_url: str, pr: PositionReport, client: aiohttp.ClientSession
):
    logging.info(f"Posted position to {pos_base_url} : \n{json.dumps(pr, indent=4)}")
    async with client.post(url=pos_base_url, data=json.dumps(pr)) as response:
        content = await response.text()
        logging.info(f"Response status received: {response.status}")
        logging.debug(f"Response received: {content}")


async def send_positions_periodically(
    pos_base_url: str,
    prs: PositionReportsPlan,
    client: aiohttp.ClientSession,
    time_start: datetime.datetime,
):
    tasks = []
    prev_time = time_start
    i = 0
    for pr in prs:
        i += 1
        next_time = prev_time + datetime.timedelta(seconds=pr.offset_ms / 1000)
        prev_time = next_time
        position_report = get_position_report_from_plan(pr, next_time)
        logging.info(f"\n Position {i} - {position_report}\n")
        await asyncio.sleep(pr.offset_ms / 1000)
        task = asyncio.create_task(post_position(pos_base_url, position_report, client))
        tasks.append(task)

    results = await asyncio.gather(*tasks)


async def send_position_reports_async(
    req_id: str,
    pos_base_url: str,
    auth_client: AuthAdapter,
    prs: PositionReportsPlan,
    time_start: datetime.datetime,
):
    auth_token = auth_client.get_headers(
        url=pos_base_url, scopes=["interuss.flight_data.position"]
    )
    async with aiohttp.ClientSession(headers=auth_token) as client:
        task2 = asyncio.create_task(
            send_positions_periodically(pos_base_url, prs, client, time_start)
        )
        await task2
        logging.info("All position reports sent")

    await client.close()
    logging.debug("Closed session")

    logging.info(f"==Req id {req_id} : Sent all position reports.")


def send_position_reports(
    req_id: str,
    pos_url: str,
    auth_client: AuthAdapter,
    prs: PositionReportsPlan,
    time_start: datetime.datetime,
):
    logging.info(f"Start req id {req_id} at {time_start}")
    wait_to_start = time_start - datetime.datetime.now()
    if wait_to_start.total_seconds() >= 0:
        time.sleep(wait_to_start.total_seconds())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        send_position_reports_async(req_id, pos_url, auth_client, prs, time_start)
    )
