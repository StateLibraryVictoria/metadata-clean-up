from os import path
from logger_config import *
from api_call import validate_mmsid
from xml_load_and_process import *

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
    if id == 0:
        return "Error"
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
    try:
        parent_id_list = [get_parent_id(load_pymarc_record(file)) for file 
                          in filepath_list 
                          if get_parent_id(load_pymarc_record(file)) is not None]
    except Exception as e:
        logger.error(f"Error iterating parent ids: {e} " 
                  +" 950 $p may be invalid or not present in some records.")
    return parent_id_list


"""
Input: list of ids.
Processing: Concatinates them to csv
Output: String
"""


def format_ids_for_api(id_list):
    try:
        string = ",".join(id_list)
        return string
    except Exception as e:
       logger.error(f"Error adding items to string: {e}")



"""
Input: List of MMS Ids, output directory, filename
Processing: Writes parent mms ids to list callable by the API function.
Output: File with mms ids separated by commas.
"""


def write_ids_to_list(id_string, output_directory, filename):
    try:
        output_location = path.join(output_directory, filename)
        output_file = open(output_location, "w", encoding="utf-8")
        output_file.write(id_string)
    except Exception as e:
        logger.error(f"Error generating mms id string from list: {e}")


"""
Input: source directory containing XML records and target output directory
Processing: Runs iterate_get_parents to get parent identifiers from source.
            Runs write_ids_to_list to create an output that can be used 
            to call the api.
Output: File that can be loaded to the API.
"""


def parent_ids_to_file(source_directory, output_directory, filename):
    try:
        file_list = get_callable_files(source_directory)
        identifiers = iterate_get_parents(file_list)
        id_string = format_ids_for_api(identifiers)
        write_ids_to_list(id_string, output_directory, filename)
        logger.info(f"{len(identifiers)} parent MMS Ids written to file.")
    except Exception as e:
        logger.error(f"Error preparing writing ids to file: {e}")


"""
Input: Source directory containing XML records
Processing: iterate_get_parents and format_ids_for_api
Output: String containing mms ids separated by commas.
"""


def parent_ids_to_string(source_directory):
    try:
        file_list = get_callable_files(source_directory)
        string_ids = iterate_get_parents(file_list)
        return string_ids
    except Exception as e:
        logger.error(f"Error getting ids as string: {e}")
