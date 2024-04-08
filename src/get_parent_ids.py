from os import path
import pymarc
from src.logger_config import *
from src.api_call import validate_mmsid
from src.xml_load_and_process import *

debug_log_config("get-parent")
logger = logging.getLogger()




def get_parent_id(pymarc_record):
    """Get parent mms id from 950 $p
        Input: record
        Processing: Passes 950 and p to get_marc_tag.
            Checks that value is a valid id.
        Output: Value or "Not present"
    """
    id = get_marc_tag(pymarc_record, "950", "p")
    if id == 0:
        return None
    if id:
        if validate_mmsid(id):
            return id
        else:
            logger.debug(f"Invalid MMS id: {id}")
            return None





def iterate_get_parents(filepath_list): #also get child MMS Id and append as a tuple.
    """Get a dictionary of index : [id, parent ids (950$p)] from records in filepath location.
        Input: .mrc or .xml filepath list from get_callable_files.

        Processing: Loads records with Pymarc. 
            Gets 001
            Gets the parent MMS ID if present.
            Adds values to a dictionary with MMS Id of record as key.
        Output: Dictionary with a index: [id, parent_id]
    """
    index = 0
    if filepath_list[0].endswith(".mrc"):
        try:
            parent_id_dict = {}
            for file in filepath_list:
                with open(file, 'rb') as fh:
                    reader = pymarc.MARCReader(fh)
                    for record in reader:
                        id = record['001'].value()
                        parent_id = get_parent_id(record)
                        if parent_id is not None:
                            parent_id_dict.update({index:[id, parent_id]})
                            index += 1
        except Exception as e:
            logger.error(f"Error reading marc from iterating parent ids: {e}")
    elif filepath_list[0].endswith(".xml"):
        try:
            parent_id_dict = {}
            for file in filepath_list:
                record = load_pymarc_record(file)
                id = record['001'].value()
                parent_id = get_parent_id(record)
                if parent_id is not None:
                    parent_id_dict.update({index : [id, parent_id]})
                    index == 1
        except Exception as e:
            logger.error(f"Error iterating parent ids: {e} " 
                    +" 950 $p may be invalid or not present in some records.")
    else:
        print("No valid files supplied. Files must be .mrc or .xml.")
        logger.error("No valid files supplied. Files must be .mrc or .xml.")
    return parent_id_dict


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
