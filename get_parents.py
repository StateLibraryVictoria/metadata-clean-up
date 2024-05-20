import os
import re
import time
import sys
from src.shared_functions import *
from src.get_parent_ids import *
from src.api_call import *

"""Set up logging"""

# Make logging directory
if not os.path.exists("logs"):
    os.mkdir("logs")
# Configure logging
timestr = time.strftime("%Y%m%d-%H%M%S")
logger_name = f"logs/get_parent_records{timestr}.log"
logger = setup_logger(name=None, log_file=logger_name)
print("Created log file with title: " + logger_name)
print("")

"""Debugging flag - use to prevent API calls."""
downloaded_records = False

"""Set up directories"""
setup_directories()
ROOT_DIR = os.path.abspath(os.curdir)

print(
    "This process is designed to call PARENT and MANY records into the same merge file."
)

if downloaded_records:
    print("Not clearing directory, working with downloaded records.")
    logger.info("Working with existing files.")
else:
    print("This process will clear downloaded content. Continue? (y/n)")
    response = input()
    if not response.lower().startswith("y"):
        print("Ending program.")
        logger.info("User ended program.")
        sys.exit()
    clear_temporary_files()

"""Load variables"""
KEY = os.getenv("PROD_KEY")
if len(KEY) < 10:
    raise ValueError("Key is not sufficiently long.")

output_many = os.path.join("output", "mrc", "split", "many")
output_parent = os.path.join("output", "mrc", "split", "parent")
output_final = os.path.join("output", "mrc", "merge")
processed_path = os.path.join("output", "record_processing", "processed")
exception_path = os.path.join("output", "record_processing", "exceptions")
load_dir = os.path.join("input", "load", "basic")

"""Check with user"""
if not os.path.exists(load_dir):
    print(
        "Load directory does not exist. Create directory in /input/load/basic and place load file."
    )
    sys.exit()

"""Load file"""
file_list = os.listdir(load_dir)

if len(file_list) == 0:
    print("No files in load directory. Stage file and try again.")
    sys.exit()

print("\n===CHECKING STAGED FILES===\n")

for file in file_list:
    print("Staged file found: " + file)
    logger.info("Staged file: " + file)

print("Do you wish to process all files? y/n")
response = input()
if not response.lower().startswith("y"):
    print("Ending program.")
    logger.info("User ended program.")
    sys.exit()
print("")

"""Get ids from file"""
id_list = []
for file in file_list:
    if ".xls" in file:
        data = get_identifiers_from_spreadsheet(os.path.join(load_dir, file))
        for column in data.columns:
            if column.startswith("mms_id"):
                ids = data[column].to_list()
                id_list.extend(ids)
                print(f"MMS_ids found: {len(ids)} ids added to list from file {file}.")
                logger.info(
                    f"MMS_ids found: {len(ids)} ids added to list from file {file}."
                )
    else:
        with open(os.path.join(load_dir, file), "r") as f:
            ids = re.findall("99\d+7636", f.read())
            id_list.extend(ids)
            print(f"MMS_ids found: {len(ids)} ids added to list from file {file}.")
            logger.info(
                f"MMS_ids found: {len(ids)} ids added to list from file {file}."
            )

logger.info(f"Created list of ids with length {len(id_list)}")
print(f"Created list of ids with length {len(id_list)}")
logger.info("Filtering to unique values...")
print("Filtering to unique values...")

identifiers = list(set(id_list))

logger.info(f"Final list has {len(identifiers)} items")
print(f"Final list has {len(identifiers)} items\n")

"""Get MARC records from API"""
if downloaded_records:
    print("Not calling API, working with downloaded records.")
else:
    try:
        get_missing_records([], identifiers, output_many, KEY)
    except Exception as e:
        print(f"Error retrieving bibs: {e}")
        logger.error(f"Error retrieving bibs: {e}")

"""Print relevant info to user"""
num_files = len(os.listdir(output_many))
print("")
print(f"Number of files captured: {num_files}")
print(f"Files written to: {output_many}")


"""Get PARENT records from API"""
record_files = get_callable_files(output_many)
parent_id_list = iterate_get_parents(record_files, True)
parent_id_list = list(set(parent_id_list))
logger.info(parent_id_list)
print("Number of parent IDs: " + str(len(parent_id_list)))

"""Call API to retrieve parent bibs"""
if downloaded_records:
    print("Not calling API, working with downloaded records.")
else:
    try:
        get_missing_records([], parent_id_list, output_many, KEY)
    except Exception as e:
        print(f"Error retrieving bibs: {e}")
        logger.error(f"Error retrieving bibs: {e}")


"""Create merge file"""
merge_file = os.path.join(output_final, f"merged_marc_records_{timestr}.mrc")
if os.path.isfile(merge_file):
    logger.info("Existing merge file. Removing file before merging records.")
    os.remove(merge_file)
merge_marc_records(output_many, merge_file)

"""Create .mrk and validation report"""
if os.path.isfile(merge_file):
    file_path, file_name = os.path.split(merge_file)
    output_file_with_validation(
        merge_file, file_path, output_filename=file_name, merged=True
    )
else:
    print("No valid records written to file.")

print(f"Records written to {merge_file}")
logger.info(f"Records written to {merge_file}")
