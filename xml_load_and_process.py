import pymarc
import os
import logging
from logger_config import *

debug_log_config("load-xml")
logger = logging.getLogger()

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
        logger.debug(f"Error getting field {field} ${subfield} from " 
                     + pymarc_record.title() 
                     + " Mms id: " + pymarc_record['001'].value())


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
    try:
        for root, dirs, files in os.walk(dir_name):
            for file in files:
                filename = path.join(dir_name, file)
                output_list += [filename]
        return output_list
    except Exception as e:
        logger.error(f"Error getting callable files: {e}")
