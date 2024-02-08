import logging
import requests
import os
import sys
from dotenv import load_dotenv
from logger_config import *

"""
Check number of API calls remaining.

Checks the number of remaining calls across the network and will exit if they drop 
below a limit.
"""


def api_volume_check(api_return):
    remaining_calls = int(api_return.headers["X-Exl-Api-Remaining"])
    limit = 100000
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


"""
Takes a list of mms ids separated by commas.
Creates a dictionary with numbered keys, each containing a list of 100 mms ids
"""


def chunk_identifiers(identifiers):
    id_list = identifiers.split(",")
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
    return request_dict


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
load_dotenv()
logger.debug("Loaded dotenv")
alma_asiapacific = os.getenv("alma_asiapacific")
alma_bibs = os.getenv("alma_bibs")
# One MMS id as a string
mms_id = os.getenv("mms_id")
## Must be a list of ids separated by commas.
mms_ids_small = os.getenv("mms_ids")
mms_ids_large = os.getenv("mms_ids_large")  # 493 ids
mms_ids_medium = os.getenv("mms_ids_medium")  # 101 ids
key = os.getenv("sandbox_key")
network = "other_system_id"
logger.debug("Loaded environment variables")

"""
Build query

Query can take a string with up to 100 MMS ids with commas in betweeen.

Possible to search for single IE values using query = {"other_system_id": "IEnumber"}

The chunk_identifiers function will break string of identifiers into batches of 100 or less.

A single call can find an IE by setting the key in the query param to "other_system_id" 
"""
identifier_batches = chunk_identifiers(mms_ids_large)
print(
    "Number of queries required to get all bibs: " + str(len(identifier_batches.keys()))
)
baseurl = "".join((alma_asiapacific, alma_bibs))
headers = {"Authorization": "apikey " + key, "Accept": "application/json"}
logger.debug("Testing chunk of mms ids")
# query = {network: "IE"}

## Queries the API and saves the response to api_call
for key in identifier_batches:
    query = {"mms_id": identifier_batches.get(key)}
    api_call = requests.get(baseurl, params=query, headers=headers)
    logger.debug("API GET request sent")
    logger.debug(api_call)
    if api_call.status_code == 400:
        print(
            "\nInvalid API Key = confirm permissions",
        )
        logger.debug("status code: " + str(api_call.status_code))
        logger.error("Test API call failed")
        sys.exit()
    elif api_call.status_code != 200:
        print("error")
        logger.debug("status code: " + str(api_call.status_code))
        logger.error("API call error")
        sys.exit()
    else:
        print("OK")
        api_volume_check(api_call)
        ## Write record to file
        try:
            file = open(f"api-records-json-group-{key}.txt", "w")
            file.write(api_call.text)
            logger.debug("output to file")
        except Exception as e:
            logger.debug(f"Error occured: {e}")
        logger.debug("API call successful")
