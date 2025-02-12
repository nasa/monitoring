from typing import List
import logging
from monitoring.monitorlib.fetch import Query
import json
import os

from implicitdict import ImplicitDict

from monitoring.position_reporter import POS_REP_LOG_DIR


def get_flight_logs(flight_id: str, order: int) -> List[Query]:
    logging.info(f"Getting logs for flight_id {flight_id} and order {order}")
    logs = []
    for fname in os.listdir(POS_REP_LOG_DIR):
        # Parse the interaction time from the file name:
        fname_parts = (os.path.splitext(fname)[0]).split("_")
        if len(fname_parts) != 2:
            logging.warning(
                f"Skipping file {fname} as it does not match the expected format"
            )
            continue
        if fname_parts[0] == flight_id:
            if order > -1:
                if int(fname_parts[1]) == order:
                    logs.append(get_query(fname))
                    return logs
                continue
            logs.append(get_query(fname))

    return logs


def get_query(filename: str) -> Query:
    with open(os.path.join(POS_REP_LOG_DIR, filename), "r") as f:
        try:
            obj = json.load(f)
            q = ImplicitDict.parse(obj, Query)
        except (KeyError, ValueError) as e:
            msg = f"Error occurred in reading logs from file {filename}: {e}"
            raise type(e)(msg)
    return q
