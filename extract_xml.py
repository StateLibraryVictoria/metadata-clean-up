import json
import logging
from os import getenv
from logger_config import *

debug_log_config("extract-xml")
logger = logging.getLogger()

"""
Generates a list of records as dictionary "mms_id" : "xml" key value pairs.
"""


def get_record(json_file):
    bibs = json.loads(json_file)
    logger.debug("json loaded")
    records = {}
    for item in bibs["bib"]:
        for key in item:
            if key == "anies":
                records.update({item["mms_id"]: item["anies"]})
    return records


FILE = getenv("JSON_RECORD")
opened = open(FILE, "r", encoding="utf-8", errors="backslashreplace")
read = opened.read()

try:
    records = get_record(read)
    logger.debug("Records loaded to dictionary")
except Exception as e:
    logger.error(f"Error loading records: {e}")

for key in records:
    file = open(f"record_{key}.xml", "w", encoding="utf-8", errors="backslashreplace")
    file.write(records[key][0])
    file.close()
