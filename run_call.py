from api_call import *
"""
Local variables
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

"""
Main program
Generates the list of ids from the original string.
Generates the dictionary of chunks from the list.

Checks if the API key is valid, then iterates through the chunks.
Each API response is parsed from josn, then written to a file in a subfolder titled json.
"""
list_ids = split_identifiers(MMS_IDS)
chunked_calls = chunk_identifiers(list_ids)

if check_api_key():
    for key in chunked_calls:
        response = get_bibs(key, chunked_calls[key])
        parsed_json = get_json_string(response)
        output_bib_files("json", key, parsed_json)
