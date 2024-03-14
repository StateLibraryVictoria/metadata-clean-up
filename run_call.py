from api_call import *
from extract_xml import *
from xml_load_and_process import *

"""
Local variables
"""

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
Each API response is parsed from josn, then written to a file 
in a subfolder titled json.
"""

print(
    "This process is currently configured to call the API based on " 
    + "a list of MMS Ids, transform them into XML, and return a "
    + "list of parent MMS Ids found in the records."
)
print("Do you wish to continue? (y/n)")
user_input = input()

if user_input.lower().startswith("y"):
    print("Running program...")
else:
    print("Exiting program")
    sys.exit()

# api_call

list_ids = split_identifiers(MMS_IDS)
chunked_calls = chunk_identifiers(list_ids)

if check_api_key():
    for key in chunked_calls:
        response = get_bibs(key, chunked_calls[key])
        parsed_json = get_json_string(response)
        output_bib_files("json", key, parsed_json)


# extract_xml

source_directory = path.join("json")
output_directory = path.join("output", "xml")

iterate_directory(source_directory, output_directory)

# xml_load_and_process


"""
Still under development. Requires a write function to
output list of ids to useful list.
"""

#xml_path = os.path.join("output", "xml")
#output_path = os.path.join("output", "parent_id")
# List for storing MMS Ids retrieved from 950$p
#parent_ids = []

#files = get_callable_files(xml_path)
#parent_ids = iterate_get_parents(files)

