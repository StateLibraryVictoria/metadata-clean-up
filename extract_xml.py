import json
import logging
from os import getenv, path, walk
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


"""
Input: filename.
Output: filestream.
"""


def open_files(filename):
    file = open(filename, "r", encoding="utf-8", errors="backslashreplace")
    file_loaded = file.read()
    return file_loaded

"""
Input: dictionary with mms id keys and xml records.
Output: Record to file in ./output/xml

"""

def write_records(dictionary):
    for key in dictionary:
        file = open(path.join("output","xml",f"record_{key}.xml"), "w", encoding="utf-8", errors="backslashreplace")
        file.write(dictionary[key][0])
        logger.debug(f"Created file for record: {key}")
        file.close()

"""
Input: directory where the files are held.
    Calls the following methods:
    - open_files
    - get_records
    - write_records
Output: writes the files to the desired location.
"""


def iterate_directory(dir_name):
    for file in walk(dir_name):
        try:
            data = open_files(file)
            records = get_record(data)
            write_records(records)
        except Exception as e:
            logger.error(f"Error occured: {e}")
            break
    return True



## Test file 
#FILE = getenv("JSON_RECORD")
#json_request = open(FILE), "r", encoding="utf-8", errors="backslashreplace")
#json_loaded = json_request.read()

# Main call:

iterate_directory(path.join("json"))