import os
import pymarc
from api_call import *
from xml_load_and_process import *
from logger_config import *


logger = logging.getLogger(__name__)
debug_log_config("log_file")
logger.info("==Shared function script logging==")

def setup_directories():
    log_path = os.path.join("logs")
    input_path = os.path.join("input","load")
    processed_path = os.path.join("output", "record_processing","processed")
    exception_path = os.path.join("output", "record_processing","exceptions")
    output_path_mrc = os.path.join("output", "mrc","split")
    input_path_mrc = os.path.join(input_path, "mrc")
    output_path_xml = os.path.join("output","xml")
    parent_records_path = os.path.join(output_path_mrc,"parent")
    many_records_path = os.path.join(output_path_mrc,"many")
    paths = [log_path, input_path, processed_path, exception_path, output_path_mrc, 
             input_path_mrc, output_path_xml, parent_records_path, many_records_path]

    for path in paths:
        if not os.path.exists(path):
            # create missing directories
            os.makedirs(path)

def split_marc_records(input_filename):
    """Splits mrc records into Parent and Many records and returns a dictionary of identifiers.

    Args:
        input_filename: str - Location and filename of target Marc file.

    Processing:
        Checks if records are Parent files, and writes those to parent_records.mrc in output/mrc/split/.
        Other records get written into many_records.mrc file in same location.
    
    Return:
        dictionary with keys: 
            'parent_records': records identified as Parent records.
            'many_records': records not identified as Parent records.
            'parent_ids': Identifiers for parent records found in 950$p of many record.
    """
    identifiers = {"parent_records":[],"many_records":[], "parent_ids":[]}
    with open(input_filename, 'rb') as fh:
        reader = pymarc.MARCReader(fh) # creates
        for record in reader:
            id = record.get_fields('001')[0].value()
            if is_parent(record):
                identifiers['parent_records'].append(id)
                output_file = os.path.join("output","mrc","split","parent",f"record_{id}.mrc")
            else:
                identifiers['many_records'].append(id)
                field_950 = record.get_fields('950')
                if len(field_950) > 0:
                    try:
                        if record['950']['p'] not in identifiers['parent_ids']:
                            identifiers['parent_ids'].append(record['950']['p'])
                    except KeyError:
                        logger.info("950 p not present in record.")
                output_file = os.path.join("output","mrc","split","many",f"record_{id}.mrc")
            f = open(output_file, 'wb')
            f.write(record.as_marc())
    return identifiers

def get_missing_records(parent_records, parent_ids, output_directory):
    """Call API process to add missing parent records to existing file.

    Args:
        parent_records: list (str) - identifiers for parent records in current batch.
        parent_ids: list (str) - identifiers located in many records required for processing.
        output_file: str - MARC file with filepath to write retrieved records to.

    Processing:
        Checks parent_ids not in parent_records. Prepares and calls API to retrieve missing records.
        Writes them to file.
    """
    # Check what identifiers need to be retrieved.
    missing_list = []
    for identifier in parent_ids:
        if identifier not in parent_records:
            missing_list.append(identifier)

    # Retrieve records.
    required = chunk_identifiers(missing_list)
    xml = "<collection>" # Wraps xml in root element collection
    if check_api_key():
        for key in required:
            response = get_bibs(key, required[key])
            string = get_json_string(response)
            bibs = json.loads(string)
            for item in bibs["bib"]:
                for key in item:
                    if key == "anies":
                        value = item["anies"][0].replace('<?xml version="1.0" encoding="UTF-16"?>', "")
                        xml += value
    xml += "</collection>" # Closes root element wrapping.
    with open("output//xml//parents_retrieved.xml","w", encoding="utf-8",errors='backslashreplace') as out:
        out.write(xml)

    # Load xml to pymarc Record object array.
    record_array = pymarc.parse_xml_to_array("output//xml//parents_retrieved.xml")
    
    # Write to mrc.
    for record in record_array:
        id = record.get_fields('001')[0].value()
        output_file = os.path.join(output_directory, f"record_{id}.mrc")
        with open(output_file, 'wb') as mrc_out:
            mrc_out.write(record.as_marc())