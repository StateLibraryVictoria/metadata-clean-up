from os import path
from logger_config import *
from api_call import validate_mmsid
from xml_load_and_process import get_marc_tag, load_pymarc_record

debug_log_config("get-parent")
logger = logging.getLogger()

"""
Input: record
Processing: Passes 950 and p to get_marc_tag.
            Checks that value is a valid id.
Output: Value or "Not present"
"""


def get_parent_id(pymarc_record):
    id = get_marc_tag(pymarc_record, "950", "p")
    if id:
        if validate_mmsid(id):
            return id
        else:
            logger.debug(f"Invalid MMS id: {id}")
            return "invalid mms id"

"""
Input: Filepath list from get_callable_files.
Processing: Loads records with Pymarc. 
            Gets the parent MMS ID if present.
            Adds unique values to list.
Output: List of IDs
"""


def iterate_get_parents(filepath_list):
    parent_id_list = []
    for file in filepath_list:
        try:
            record = load_pymarc_record(file)
            value = get_parent_id(record)
            if value is not None and value not in parent_id_list:
                parent_id_list.append(value)
        except Exception as e:
            logger.error(f"Error iterating parent ids: {e} for file {file}")
    return parent_id_list


"""
Input: list of ids.
Processing: Concatinates them to csv
Output: String
"""


def format_ids_for_api(id_list):
    string = ""
    if type(id_list) == list:
        for item in list:
            string += item + ","
    ids = string[0:-1]
    return ids


"""
Input: List of MMS Ids, output directory, filename
Processing: Writes parent mms ids to list callable by the API function.
Output: File with mms ids separated by commas.
"""


def write_ids_to_list(id_list, output_directory, filename):
    try:
        ids = format_ids_for_api(id_list)
        output_location = path.join(output_directory, f"{filename}.txt")
        output_file = open(output_location, "w", encoding="utf-8")
        output_file.write(ids)
    except Exception as e:
        logger.error(f"Error generating mms id string from list: {e}")


"""
Input: source directory containing XML records and target output directory
Processing: Runs iterate_get_parents to get parent identifiers from source.
            Runs write_ids_to_list to create an output that can be used 
            to call the api.
Output: File that can be loaded to the API.
"""


def parent_ids_to_file(source_directory, output_directory):
    try:
        identifiers = iterate_get_parents(source_directory)
        write_ids_to_list(identifiers, output_directory)
    except Exception as e:
        logger.error(f"Error preparing writing ids to file: {e}")
