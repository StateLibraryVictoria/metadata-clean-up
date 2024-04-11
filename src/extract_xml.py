import json
import logging
from os import getenv, path, walk
from src.logger_config import *

debug_log_config("extract-xml")
logger = logging.getLogger()




def get_record_from_json(json_object):
    """
    Input: json file
    Processing: json.loads(file) converts ASCII backslash replaced characters with UTF-8.
    Generates a list of records as dictionary "mms_id" : "xml" key value pairs.
    """

    bibs = json.loads(json_object)
    logger.debug("Json loaded from api output")
    records = {}
    for item in bibs["bib"]:
        for key in item:
            if key == "anies":
                records.update({item["mms_id"]: item["anies"]})
    return records


def iterate_returned_requests(dir_name, output_dir):
    """Processes json files retrieved from Alma API to xml records.

    args:
        dir_name (path) - location of json files.
        output_dir (path) - output directory for xml files.
        
    Processing:
        - Opens each file in the directory.
        - Gets MARCxml record from json as a dict of 'mms_id':'xml'.
        - Strips header which contains incorrect encoding.

    Output: writes the files to the desired location.
    """
    logger.debug("Inside iterate_directory")
    for root, dirs, files in walk(dir_name):
        logger.debug(files)
        log_list = []
        for file in files:
            filename = path.join(dir_name, file)
            try:
                with open(filename, "r", encoding="utf-8", errors="backslashreplace") as json_file:
                    json = json_file.read()
                records = get_record_from_json(json)
                for key in records:
                    try:
                        records.update({key:(fix_xml_header_encoding(records[key][0]))})
                        with open(path.join(output_dir, f'record_{key}.xml', 'w',encoding="utf-8", errors="backslashreplace",)) as file:
                                file.write(records[key])
                                log_list.append(key)
                    except Exception as e:
                        logger.error(f"Error updating encoding for record {key}: {e}")
                logger.info("Records written to: " + output_dir)
                final_list = ";".join(log_list)
                logger.debug(f"Created file for records: {final_list}")
            except Exception as e:
                logger.error(f"Error occured while iterating dictionary: {e}")
                break
        return True


def fix_xml_header_encoding(xml_record):
    """Strips xml header encoding from xml records supplied as strings.
    """
    if '<record>' in xml_record:
        if xml_record.startswith('<?xml version'):
            xml_record = xml_record.replace('<?xml version="1.0" encoding="UTF-16"?>', "")
        return xml_record
    else:
        print("Could not find tag <record> in data.")
        return None
