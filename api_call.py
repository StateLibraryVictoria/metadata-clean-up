import logging
import json
import requests
import os
import sys
from datetime import datetime
from logger_config import *


"""
Takes an API call.
Output is EXIT if the number is below API_CALL_LIMIT else True.
"""


def api_volume_check(api_return):
    remaining_calls = int(api_return.headers["X-Exl-Api-Remaining"])
    limit = API_CALL_LIMIT
    if remaining_calls < limit:
        print(
            f"WARNING: Remaining API calls ({remaining_calls}) is less than limit: {limit}."
        )
        print(f"Too few API calls remaining. Quitting...")
        logger.warning(
            f"Remaining API calls at or below limit of {limit}. Request cancelled."
        )
        sys.exit()
    else:
        print(f"Remaining API calls: {remaining_calls}.")
        logger.info(f"Remaining API calls: {remaining_calls}. Request continues...")
        return True


"""
Takes an MMS Id.
Outputs a boolean where valid id is True.
"""


def validate_mmsid(mms_id):
    if mms_id.startswith("99") and mms_id.endswith("7636") and len(mms_id) > 6:
        return True
    else:
        return False


"""
Takes a string of MMS Ids separated by commas. 
    Checks each one is a valid MMS Id.
Outputs a list of valid MMS ids (bad values added to log).
"""


def split_identifiers(identifiers):
    id_list = identifiers.split(",")
    bad_ids = []
    for id in id_list:
        logger.warning(f"Id in for loop is: {id}")
        if not validate_mmsid(id):
            logger.error(f"Validation error for MMS id, id removed from API call: {id}")
            bad_ids += [id]
    if len(bad_ids) > 0:
        print(
            f"WARNING: {len(bad_ids)} MMS Ids were invalid. Removed from query. Consult logfile for more information."
        )
        logger.error(f"{len(bad_ids)} MMS Ids were invalid.")
        for id in bad_ids:
            id_list.remove(id)
    return id_list


"""
Takes a list of mms ids.
Outputs a dictionary with 100 records in each key.
"""


def chunk_identifiers(id_list):
    counter = 0
    request_dict = {}
    while len(id_list) > 100:
        list_slice = id_list[0:100]
        request_dict.update({str(counter): ",".join(list_slice)})
        logger.debug(f"Created chunk with key: {counter}")
        counter += 1
        del id_list[0:100]
        logger.debug(f"Removed items added to chunk {counter - 1} from original list.")
    if len(id_list) > 0:
        logger.debug(f"List has remainder of: {str(len(id_list))}")
        request_dict.update({str(counter): ",".join(id_list)})
    print(
        "Number of queries required to get all bibs: " + str(len(request_dict.keys()))
    )
    return request_dict


"""
Input is query to Alma API.
Output is boolean except if api_volume_check() fails.
"""


def check_api_key():
    headers = {"Authorization": "apikey " + KEY, "Accept": "application/json"}
    response = requests.get(BASEURL + "test", headers=headers)
    logger.debug(response)
    if response.status_code == 200:
        api_volume_check(response)
        return True
    else:
        print("Invalid API key, confirm permissions.")
        logger.error("API call unsuccessful. Check key.")
        return False


"""
Input will be a batch of MMS ids.
Output will be an API response.
"""


def get_bibs(part, mms_ids):
    headers = {"Authorization": "apikey " + KEY, "Accept": "application/json"}
    query = {"mms_id": mms_ids}
    api_call = requests.get(BASEURL, params=query, headers=headers)
    logger.debug(f"API GET request sent. Batch number {part}")
    logger.debug(api_call)
    return api_call


"""
Input is API call.
Output is pretty JSON.
"""


def get_json_string(api_call):
    data = api_call.json()
    json_str = json.dumps(data, indent=4)
    return json_str


"""
Input is output folder, request part, and data input.
Output is a file.
"""


def output_bib_files(dir, part, input):
    today = datetime.now().strftime("%Y%m%d%H%M00")
    filename = os.path.join(dir, f"{today}_records_batch_{part}.json")
    try:
        file = open(filename, "w", encoding='utf-8', errors='backslashreplace')
        file.write(input)
        logger.debug("output to file")
        file.close()
    except Exception as e:
        logger.debug(f"Error occured: {e}")


""" 
Configure logfile. 

Creates a log file with the name log_api_call.log that will capture actions that happen
during the API call.
Every time the script is run it will append log to the same file.

Logger calls are used throughout the program and will record hidden info including the http request.
"""
debug_log_config("api_call")
logger = logging.getLogger()

## Loads environment variables
# One MMS id as a string
MMS_ID = os.getenv("MMS_ID")
## Must be a list of ids separated by commas.
MMS_IDS = os.getenv("MMS_IDS")
# Alma API key
KEY = os.getenv("KEY")
logger.debug("Loaded environment variables")

# Local variables
API_CALL_LIMIT = 10000
BASEURL = "https://api-ap.hosted.exlibrisgroup.com/almaws/v1/bibs/"


