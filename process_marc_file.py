import os
from sys import exit
from copy import deepcopy
import time
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.transform_marc_file import *


"""Set up logging"""

# Make logging directory
if not os.path.exists("logs"):
    os.mkdir("logs")
# Configure logging
timestr = time.strftime("%Y%m%d-%H%M%S")
logger_name = f"logs/process_marc_file_{timestr}.log"
logger = setup_logger(name=None, log_file=logger_name)
print("Created log file with title: " + logger_name)
print("")

# Debugging flag - set to True to work with existing records or False to start from scratch.
downloaded_records = False

# Setup workspace
setup_directories()

KEY = os.getenv("KEY", None)
if KEY is None:
    print("API Key is None. Exiting.")
    sys.exit()
output_path = os.path.join("output", "mrc", "split")
input_path = os.path.join("input", "load", "mrc")
parent_records_path = os.path.join(output_path, "parent")
many_records_path = os.path.join(output_path, "many")
merge_path = os.path.join("output", "mrc", "merge")
valid_output = os.path.join(merge_path, "updated_records.mrc")
invalid_output = os.path.join(merge_path, "records_with_exceptions.mrc")
start_fresh = False

if downloaded_records:
    print("Not clearing directory, working with downloaded records.")
else:
    """Determine if the user wants to call all ids, or process existing file"""
    print(
        "This process can be run with supplied records (calling only missing records) or on an older file of records by calling the ids from scratch."
    )
    print("Re-download records for all ids found? (y/n)")
    response = input()
    if response.lower().startswith("y"):
        print("Process will download all identified records via the API.")
        logger.info("Identifying and downloading all records.")
        start_fresh = True
    else:
        print("Process will only call missing Parent records.")
        logger.info("Processing file with supplied records.")
        print("Clearing up temporary files.")
        clear_temporary_files()

# Check only one file in input directory and process.
for root, dir, files in os.walk(input_path):
    output_list = [os.path.join(input_path, file) for file in files]
    if len(output_list) == 0:
        print(
            "No files in input directory. Add files to /input/load/mrc. "
            + "Ending program."
        )
        exit()
    else:
        print("The following files have been found:")
        for file in output_list:
            print(file)
        print(f"Continue processing? (y/n)")
        response = input()
        if not response.lower().startswith("y"):
            exit()

# split the files
many_records = []
parent_records = []
parent_ids = []
id_dictionary = {}
for file in output_list:
    identifiers = split_marc_records(file)
    many_records.extend(identifiers["many_records"])
    parent_records.extend(identifiers["parent_records"])
    parent_ids.extend(identifiers["parent_ids"])
    for key in identifiers["parent_many_dict"]:
        if key in id_dictionary:
            new_list = id_dictionary[key].extend(identifiers["parent_many_dict"][key])
            id_dictionary.update({key: new_list})
        else:
            id_dictionary.update({key: identifiers["parent_many_dict"][key]})

if start_fresh and not downloaded_records:
    # clear directories
    clear_temporary_files()

    many_records = list(set(many_records))
    many_records.sort()

    parent_ids = parent_records + parent_ids

    # Get many records
    get_missing_records([], many_records, many_records_path)


parent_ids = list(set(parent_ids))
parent_ids.sort()

# get required parents
get_missing_records(parent_records, parent_ids, parent_records_path)

parent_files = [
    os.path.join(parent_records_path, filename)
    for filename in os.listdir(parent_records_path)
]
many_files = [
    os.path.join(many_records_path, filename)
    for filename in os.listdir(many_records_path)
]

## Basic cleanup loop.
exceptions = []
valid_file = ""

for key in id_dictionary:
    filename = f"record_{key}.mrc"
    many_filenames = [f"record_{id}.mrc" for id in id_dictionary[key]]
    with open(os.path.join(parent_records_path, filename), "rb") as pf:
        p_reader = pymarc.MARCReader(pf)
        for p_record in p_reader:
            parent_rec = deepcopy(p_record)
            for file in many_filenames:
                with open(os.path.join(many_records_path, file), "rb") as mf:
                    reader = pymarc.MARCReader(mf)
                    for record in reader:
                        wr = deepcopy(record)
                        ## Now we have both our parent record open and our many record open.
                        try:
                            fix_record = many_record_cleanup(wr, parent_rec)
                            has_exception = check_fields(
                                fix_record,
                                ("100", "110", "111", "130"),
                                ("700", "710", "711", "720", "730"),
                            )
                            if has_exception:
                                if p_record["001"].value() not in exceptions:
                                    exceptions.append(p_record["001"].value())
                                    with open(invalid_output, "ab") as output:
                                        output.write(p_record.as_marc())
                                with open(invalid_output, "ab") as output:
                                    output.write(fix_record.as_marc())
                            else:
                                with open(valid_output, "ab") as output:
                                    output.write(fix_record.as_marc())
                        except Exception as e:
                            print("Error occurred while transforming file: " + e)
                            logger.error(f"Error occurred while transforming file: {e}")
                            exceptions.append(fix_record["001"].value())
                            with open(invalid_output, "ab") as output:
                                output.write(fix_record.as_marc())


# Validate and return how many records failed.
if os.path.isfile(valid_output):
    valid_path, valid_name = os.path.split(valid_output)
    output_file_with_validation(
        valid_output, valid_path, output_filename=valid_name, merged=True
    )
else:
    print("No valid records written to file.")

# check file exists
if os.path.isfile(invalid_output):
    invalid_path, invalid_name = os.path.split(invalid_output)
    output_file_with_validation(
        invalid_output, invalid_path, output_filename=invalid_name, merged=True
    )
else:
    print("No exceptions written to file.")

# Build archive file of unmodified MANY records.
many_records_path
output_file_with_validation(
    many_records_path, merge_path, output_filename="unedited_many_backup.mrc"
)
