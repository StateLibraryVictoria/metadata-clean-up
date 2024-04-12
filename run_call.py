from src.api_call import *
from src.extract_xml import *
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.logger_config import *
import pymarc
import shutil
from io import StringIO
import pandas as pd

logger = logging.getLogger()

"""
Local variables
"""

## Loads environment variables
# One MMS id as a string
MMS_ID = os.getenv("MMS_ID") # used for testing changes to script
## Must be a list of ids separated by commas.
MMS_IDS = os.getenv("MMS_IDS")
# Alma API key
KEY = os.getenv("KEY")
logger.debug("Loaded environment variables")

# Local variables

BASEURL = "https://api-ap.hosted.exlibrisgroup.com/almaws/v1/bibs/"

"""
Main program
Generates the list of ids from the original string.
Generates the dictionary of chunks from the list.

Checks if the API key is valid, then iterates through the chunks.
Each API response is parsed from josn, then written to a file 
in a subfolder titled json.
"""

# setup directories
setup_directories()


print(
    "This process is currently configured to call the API based on " 
    + "a list of MMS Ids, get their parent records, transform the data,"
    + " and output to /output/mrc/ with MarcEdit validation."
)
print("All temporary files in the following directories will be deleted:" 
      + "\n/json \n/output/mrc/split \n/output/mrc/merge")
print("Do you wish to continue? (y/n)")
user_input = input()

if user_input.lower().startswith("y"):
    print("Running program...")
else:
    print("Exiting program")
    sys.exit()

# make sure iterative directories are clear of files
clear_temporary_files()

# api_call
list_ids = split_identifiers(MMS_IDS)
chunked_calls = chunk_identifiers(list_ids)

print("Retrieving records from API based on MMS Id list...")
if check_api_key():
    for key in chunked_calls:
        response = get_bibs(key, chunked_calls[key])
        parsed_json = get_json_string(response)
        output_json_files("json", key, parsed_json)


# extract_xml
source_directory = path.join("json")
for root, dirs, files in os.walk(source_directory):
    filenames = [os.path.join(source_directory, file) for file in files]

# parse xml to MARC
output_directory = os.path.join("output","mrc","split","many")
for filename in filenames:
    record_list = []
    with open(filename, 'r') as file:
        file = file.read()
        records = get_record_from_json(file)
        for key in records:
            record = fix_xml_header_encoding(records[key][0])
            record_object = pymarc.parse_xml_to_array(StringIO(record))
            record_list.append(record_object[0])
            logger.debug(record)
        logger.info(f"Records added: {len(record_list)}")
        for record in record_list:
            id = record.get_fields('001')[0].value()
            output_file = os.path.join(output_directory, f"record_{id}.mrc")
            with open(output_file, 'wb') as mrc_out:
                mrc_out.write(record.as_marc())


# get parent ids from records
record_files = get_callable_files(output_directory)
parent_ids = iterate_get_parents(record_files, parent_only=True)
logger.info(parent_ids)
output_dir_parent = os.path.join("output", "mrc", "split", "parent")

# get parent records
print("Retrieving matched Parent records from API...")
try:
    get_missing_records([], parent_ids, output_dir_parent)
except Exception as e:
    print(f"Error retrieving bibs: {e}")
    logger.error(f"Error retrieving bibs: {e}")

# process records
parent_files = get_callable_files(output_dir_parent)
logger.info(parent_files)
merge_path = os.path.join("output","mrc","merge")
valid_output = os.path.join(merge_path, "updated_records.mrc")
valid_written_to = False
invalid_output = os.path.join(merge_path, "records_with_exceptions.mrc")
invalid_written_to = False

# cleanup existing output files
if os.path.isfile(valid_output):
    os.remove(valid_output)
    logger.info("Cleaned existing valid file output.")
if os.path.isfile(invalid_output):
    os.remove(invalid_output)
    logger.info("Cleaned existing invalid file output.")

# process marc files
for filename in record_files:
    with open(filename, 'rb') as wf:
        reader = pymarc.MARCReader(wf)
        for record in reader:
            fix_record = deepcopy(record)
            mms_id = fix_record['001'].value()
            parent = get_parent_id(fix_record)
            if parent is not None:
                parent_file = os.path.join(output_dir_parent, f"record_{parent}.mrc")
                try:
                    with open(parent_file, 'rb') as pf:
                        p_reader = pymarc.MARCReader(pf)
                        for p_record in p_reader:
                            fix_record = big_bang_replace(fix_record, p_record)
                            fix_record = fix_indicators(fix_record)
                            fix_record = fix_655_gmgpc(fix_record)
                except Exception as e:
                    print(f"Parent file for {mms_id} not in output directory. Parent Id searched: {parent}")
                    logger.warning(f"Parent MMS Id for {mms_id} not in output directory. Parent Id searched: {parent}")
            # IMPLEMENT VALIDATION
            valid = True
            # output file based on validation
            if (valid):
                try:
                    with open(valid_output, 'ab') as valid:
                        valid.write(fix_record.as_marc())
                    valid_written_to = True
                except Exception as e:
                    logger.error(f"Error writing record to merge file: {e}")    
            else:
                try:
                    with open(invalid_output, 'ab') as invalid:
                        invalid.write(fix_record.as_marc())
                    invalid_written_to = True
                except Exception as e:
                    logger.error(f"Error writing record to merge file: {e}")

# output_file_with_validation for each file that has output
if (valid_written_to):
    final = os.path.join("output","mrc")
    print("MARC file with valid records created.")
    shutil.copyfile(valid_output, os.path.join(final, "valid_load_file.mrc"))
    output_file_with_validation(valid_output, os.path.join("output","mrc"),filename="valid_load_file.mrc", merged=True)
if (invalid_written_to):
    print("MARC file for records with exceptions created.")
    shutil.copyfile(invalid_output, os.path.join(final, "invalid_review_file.mrc"))
    output_file_with_validation(invalid_output, final, filename="invalid_review_file.mrc", merged=True)


  