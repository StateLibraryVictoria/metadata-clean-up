import logging
import requests
import os
import sys

logger = logging.getLogger()

API_CALL_LIMIT = 10000


def api_volume_check(api_return):
    """Returns True if remaining API calls above API_CALL_LIMIT"""
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


def validate_mmsid(mms_id):
    """Validate MMS ID based on SLV configuration"""
    if mms_id.startswith("9999") and mms_id.endswith("76367636"):
        print(
            f"Probable invalid MMS Id requires review: {mms_id}. Validity check returning False."
        )
        logger.warning(f"Probable invalid MMS Id: {mms_id}")
        return False
    elif mms_id.startswith("99") and mms_id.endswith("7636") and len(mms_id) > 6:
        return True
    else:
        return False


def split_identifiers(identifiers):
    """Taks a comma separated string of identifiers and checks all values are valid. Bad values are added to log."""
    id_list = identifiers.split(",")
    bad_ids = []
    for id in id_list:
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


def chunk_identifiers(id_list):
    """Convert list of identifiers into chunks of 100 identifiers

    Returns:
        Dictionary.
        Keys are numbers from 0 - number of keys.
        Values (str) 100 identifiers separated by commas.
    """
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


BASEURL = "https://api-ap.hosted.exlibrisgroup.com/almaws/v1/bibs/"

KEY = os.getenv("KEY", None)


def check_api_key():
    """Makes a test call to the API and returns a boolean."""
    if KEY == None:
        logger.info("Check API Key: Key not configured in API call.")
        return None
    headers = {"Authorization": "apikey " + KEY, "Accept": "application/json"}
    response = requests.get(BASEURL + "test", headers=headers)
    logger.info(response)
    if response.status_code == 200:
        api_volume_check(response)
        return True
    else:
        print("Invalid API key, confirm permissions.")
        logger.error("API call unsuccessful. Check key.")
        return False


def get_bibs(part, mms_ids):
    """Query API for bibliographic records. Assumes mutliple calls will be passed.

    Args:
        part (str) | Number as string representing the chunk of identifiers being sent to API.
        mms_ids (str) | Up to 100 MMS Ids separated by commas.

    Returns:
        Api response (JSON)
    """
    if KEY == None:
        logger.info("Get bibs: Key not configured in API call.")
        return None
    headers = {"Authorization": "apikey " + KEY, "Accept": "application/json"}
    query = {"mms_id": mms_ids}
    api_call = requests.get(BASEURL, params=query, headers=headers)
    logger.debug(f"API GET request sent. Batch number {part}")
    logger.debug(api_call)
    return api_call
