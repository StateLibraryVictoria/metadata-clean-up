from os import path
from copy import deepcopy
import pymarc
from src.logger_config import *
from src.api_call import validate_mmsid
from src.shared_functions import get_callable_files

debug_log_config("get-parent")
logger = logging.getLogger()


def big_bang_replace(many_record, parent_record):
    """Replaces fields based on the big bang cleanup project.
    Fields 1xx, 260/264, 6xx, 7xx, 8xx are copied from parent to many record."""
    if not isinstance(many_record, pymarc.record.Record):
        raise Exception(f"Record to be updated must be a pymarc Record object. Object supplied is: {type(many_record)}, value {many_record}")
    if not isinstance(parent_record, pymarc.record.Record):
        logger.error(f"Error completing big bang replace. Parent record must be a pymarc Record object. Many record: {many_record['001'].value()}")
        return many_record
    fix_record = deepcopy(many_record)
    onexx = ['100', '110', '111', '130']
    pub_year = ['260', '264']
    subjects = ["600", "610", "611", "630", "648", "650", "651", "653", "654", "655",
            "656", "657", "658", "662", "690", "691", "696", "697", "698", "699",]
    added_entries = ["700", "710", "711", "720", "730", "740", "752", "753", "754", "790",
            "791", "792", "793", "796", "797", "798", "799",]
    series = ["800", "810", "811", "830"]
    notRepeatable = ["010","018","036","038","040","042","044","045","066","100","110","111","130","240","243","245","254", "256", "263", "306","357","507","514"]
    replace_list = [onexx, pub_year, subjects, added_entries, series]
    in_parent = []
    try:
        for list in replace_list:
            for item in list:
                count = len(parent_record.get_fields(item))
                if count == 0:
                    continue
                elif count == 1:
                    in_parent.append(item)
                elif count > 1 and item not in notRepeatable:
                    in_parent.append(item)
    except Exception as e:
        print(f"Error setting up list of present fields in parent for big bang replace: {e}")
    try:
        for item in in_parent:
            if item.startswith('1'):
                for tag in onexx:
                    fix_record.remove_fields(tag)
                for field in parent_record.get_fields(item):
                    fix_record.add_ordered_field(field)
            if item.startswith('2'):
                for tag in pub_year:
                    fix_record.remove_fields(tag)
                for field in parent_record.get_fields(item):
                    fix_record.add_ordered_field(field)
            elif item.startswith('6'):
                for tag in subjects:
                    fix_record.remove_fields(tag)
                for field in parent_record.get_fields(item):
                    fix_record.add_ordered_field(field)
            elif item.startswith('7'):
                for tag in added_entries:
                    fix_record.remove_fields(tag)
                for field in parent_record.get_fields(item):
                    fix_record.add_ordered_field(field)
            elif item.startswith('8'):
                for tag in series:
                    fix_record.remove_fields(tag)
                for field in parent_record.get_fields(item):
                    fix_record.add_ordered_field(field)
    except Exception as e:
        print(f"Error replacing fields in many record: {e}")
    return fix_record

def get_parent_id(pymarc_record):
    """Get parent mms id from 950 $p
        Input: record
        Processing: 
            Checks if 950$p in record.
            Checks that value is a valid id.
        Output: Value or "Not present"
    """
    try:
        id = pymarc_record['950']['p']
    except KeyError:
        return None
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
    filepath_list.sort()
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
                records = pymarc.parse_xml_to_array(file) 
                for record in records:
                    id = record['001'].value()
                    parent_id = get_parent_id(record)
                    if parent_id is not None:
                        parent_id_dict.update({index : [id, parent_id]})
                        index += 1
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
