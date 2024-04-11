import json
import logging
from os import getenv, path, walk
from src.logger_config import *

debug_log_config("extract-xml")
logger = logging.getLogger()


"""
Input: json file
Processing: json.loads(file) converts ASCII backslash replaced characters with UTF-8.
Generates a list of records as dictionary "mms_id" : "xml" key value pairs.
"""


def get_record(json_file):
    bibs = json.loads(json_file)
    logger.debug("Json loaded from api output")
    records = {}
    for item in bibs["bib"]:
        for key in item:
            if key == "anies":
                records.update({item["mms_id"]: item["anies"]})
    return records


"""
Input: filename.
Output: filestream.
"""


def open_files(filename):
    with open(filename, "r", encoding="utf-8", errors="backslashreplace") as file:
        file_loaded = file.read()
    return file_loaded


"""
Input: dictionary with mms id keys and xml records.
Output: Record to file in ./output/xml

"""


def write_records(dictionary, output_dir):
    log_list = []
    for key in dictionary:
        file = open(
            path.join(output_dir, f"record_{key}.xml"),
            "w",
            encoding="utf-8",
            errors="backslashreplace",
        )
        file.write(dictionary[key][0])
        log_list += [key]
        file.close()
    final_list = ";".join(log_list)
    logger.debug(f"Created file for records: {final_list}")





def iterate_directory(dir_name, output_dir):
    """
    Input: directory where the files are held.
        Calls the following methods:
        - open_files
        - get_records
        - write_records
    Output: writes the files to the desired location.
    """
    logger.debug("Inside iterate_directory")
    for root, dirs, files in walk(dir_name):
        logger.debug(files)
        for file in files:
            filename = path.join(dir_name, file)
            try:
                data = open_files(filename)
                records = get_record(data)
                fixed_header = fix_header_encoding(records)
                write_records(fixed_header, output_dir)
                logger.info("Records written to: " + output_dir)
            except Exception as e:
                logger.error(f"Error occured while iterating dictionary: {e}")
                break
        return True


"""
Input: Dictionary containing MMS Id, xml record pairs.
Processing: Replace utf-16 with utf-8 in header.
Output: Transformed dictionary
"""


def fix_header_encoding(dictionary):
    for key in dictionary:
        string = dictionary[key][0]
        string = string.replace('<?xml version="1.0" encoding="UTF-16"?>', "")
        dictionary[key][0] = string
    return dictionary
