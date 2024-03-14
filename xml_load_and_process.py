import pymarc
import os
import logging
import json
from logger_config import *
import xml.etree.ElementTree as et

debug_log_config("load-xml")
logger = logging.getLogger()
logger.info("===NEW TEST===")

"""
Input: Pymarc record object and desired field and subfield.
Processing: Checks if the field exists
Output: returns value stored in specified tag.
"""


def get_marc_tag(pymarc_record, field, subfield):
    try:
        value = pymarc_record[field][subfield]
        return value
    except:
        logger.debug(f"Error getting field.")
        return "Not present"


"""
Input: record
Processing: Passes 950 and p to get_marc_tag.
Output: Value or "Not present"
"""


def get_parent_id(pymarc_record):
    return get_marc_tag(pymarc_record, "950", "p")


"""
Input: Filepath to single xml record.
Processing: passes to pymarc
Output: First item in the array (aka the record)
"""


def load_pymarc_record(filename):
    record = pymarc.parse_xml_to_array(filename)
    return record[0]


"""
Input: Directory where target files are held
Processing: Creates filpath using directory and name
Output: List of filepaths
"""


def get_callable_files(dir_name):
    output_list = []
    for root, dirs, files in os.walk(dir_name):
        for file in files:
            filename = path.join(dir_name, file)
            output_list += [filename]
    return output_list


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
            if value not in parent_id_list:
                parent_id_list.append(value)
        except Exception as e:
            logger.error(f"Error occured: {e} for file {file}")
    return parent_id_list

