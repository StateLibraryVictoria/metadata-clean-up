import os
from sys import exit
from copy import deepcopy
from shared_functions import *
from xml_load_and_process import *
from get_parent_ids import *
from logger_config import *



logger = logging.getLogger(__name__)
debug_log_config("log_file")
logger.info("==Process marc file log==")


# Setup workspace
setup_directories()

output_path = os.path.join("output", "mrc","split")
input_path = os.path.join("input","load", "mrc")
parent_records_path = os.path.join(output_path,"parent")
many_records_path = os.path.join(output_path,"many")


# Check only one file in input directory and process.
for root, dir, files in os.walk(input_path):
    output_list = [os.path.join(input_path, file) for file in files]
    if len(output_list) == 0:
        print("No files in input directory. Add files to /input/load/mrc. Ending program.")
        exit() 
    elif len(output_list) > 1:
        print(f"Too many files in input directry. Only stage one file. Directory contains {len(output_list)} files. Ending program.")
        exit()
    else:
        filename, extension = os.path.splitext(output_list[0])
        if extension != ".mrc":
            print("File in load directory does not have expected .mrc extension. Ending program.")
            logger.warn(f"Input directory contains {filename} with extension {extension}: restage a file with extension .mrc.")
            exit()
        logger.info(f"Input directory contains {filename} with extension {extension}.")
        filepath = output_list[0]

# split the file
identifiers = split_marc_records(filepath)
many_records = identifiers["many_records"]
parent_records = identifiers["parent_records"]
parent_ids = identifiers['parent_ids']

# sort the records before the request
parent_ids.sort()

# get required parents
get_missing_records(parent_records,parent_ids,parent_records_path)

def get_ids(record):
    try:
        pid = record['950']['p']
    except KeyError:
        pid = "Not in record."
    try:
        id = record.get_fields('001')[0].value()
    except KeyError:
        id = "Value not in 001."
    return id, pid

def get_files_list(directory):
    output_array = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filename = os.path.join(directory, file)
            output_array += [filename]
    return output_array

# Get list of filenames.
parent_files = []
many_files = []
parent_files = get_files_list(parent_records_path)
many_files = get_files_list(many_records_path)

# match records against parents and replace 100, 110, 260, 264, 7xx, 830.
for file in many_files:
    reader = pymarc.MARCReader(open(file, 'rb'))
    for record in reader:
        current_record = deepcopy(record)
    try:
        parent_id = current_record['950']['p']
    except:
        print("No parent id found in record.")
    for parent_file in parent_files:
        if parent_file.endswith(f"record_{parent_id}.mrc"):
            print("Matched parent record.")
            print(parent_file)
            parent_reader = pymarc.MARCReader(open(parent_file, 'rb'))
            for record in parent_reader:
                try:
                    new_record = replace_field(current_record, record, "100")
                except Exception as e:
                    print(f"Replacing field 100 did not work. Error: {e}")
                try:
                    new_record = replace_field(new_record, record, "110")
                except Exception as e:
                    print(f"Replacing field 110 did not work. Error: {e}")
                try:
                    new_record = replace_field(new_record, record, "264")
                except Exception as e:
                    print(f"Error replacing field 264. Error: {e}")
                try:
                    new_record = replace_field(new_record, record, "260")
                except Exception as e:
                    print(f"Error replacing field 260. Error: {e}")
    with open(file, 'wb') as out:
        out.write(new_record.as_marc())