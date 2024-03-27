import pymarc
import os
import logging
import re
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
    if len(record) == 1:
        return record[0]
    else:
        print("Multi-record file identified.")
        return record


"""
Input: Directory where target files are held
Processing: Creates filpath using directory and name
Output: List of filepaths
"""


def get_callable_files(dir_name):
    output_list = []
    try:
        for root, dirs, files in os.walk(dir_name):
            files.sort()
            print(files)
            output_list = [path.join(dir_name, file) for file in files]
        return output_list
    except Exception as e:
        logger.error(f"Error getting callable files: {e}")


def get_field_count(record, field):
    """Counts number of fields in record

    Args:
        record (pymarc record object): 
        field (str): the desired field expressed as a string.
    """
    try:
        fields = record.get_fields(field)
    except Exception as e:
        logger.error(f"Error getting field count: {e}")
    return len(fields)


def get_field_from_source(source_record, field):
    """Checks for field in source record and returns value when only one example is present.

    Args:
        source_record (pymarc Record object): record containing data with target field.
        field (str | pymarc Field object): field desired to be copied.

    Returns:
        pymarc Field object where only one is present within record.
    """
    if type(field) == str:
        tag = field
    else:
        tag = field.tag
        indicators = field.indicators
        subfields = field.subfields

    # Check that field in source record.
    if tag.startswith("6"):
        return source_record.get_fields(tag)
    elif get_field_count(source_record, tag) != 1:
        amount = f"no {tag} fields" if get_field_count(source_record, tag) < 1 else f"too many {tag} fields"
        logger.warning(f"Source record contains {amount}. "
                        + "Cancelling operation.")
        return None
    else:
        logger.info(f"Source record contains field {tag}. "
                        + "Continuing operation")
        copy_field = source_record.get_fields(tag)
    return copy_field[0] if len(copy_field) == 1 else None

def add_field_to_target(target_record, field, replace=True):
    """ Returns the target record with the passed subfield. Default strips existing instances of field.

    Args:
        target_record (pymarc Record object): record requiring updating.
        field (pymarc Field object): field to be added to record.
        replace (bool): whether to keep or delete existing fields. Defaults to delete (True).

    Returns:
        pymarc Record object: transformed record.
    """
    tag = field.tag
    indicators = field.indicators
    subfields = field.subfields
        
    if replace:
        logger.info("Processing record: " + target_record.get_fields('001')[0].value())
        try: # try to remove the fields from the record to be updated
            if tag.startswith("1"):
                source_1xx = target_record.get_fields('100', '110', '111')
                logger.info(f"Removing {len(source_1xx)} subfields from record.")
                print(f"Removing {len(source_1xx)} subfields from record.")
                if len(source_1xx) > 1:
                    print("Multiple 1xx fields identified. See log for details.")
                    logger.warn("Multiple 1xx fields identified. All fields have been removed.")
                for f in source_1xx:
                    logger.info(f"Record contains field: {f.tag}")
                    print(f"Record contains field: {f.tag}")
                    target_record.remove_field(f)
                    logger.info(f"Success: " + f.tag + " " + f.format_field() + " removed from record.")
            else:
                logger.info(f"Removing {len(target_record.get_fields(tag))} subfields from record.")
                print(f"Removing {len(target_record.get_fields(tag))} subfields from record.")
                for f in target_record.get_fields(tag):
                    target_record.remove_field(f)
            logger.info(f"Success: {tag} removed from target.")
            print(f"Success: {tag} removed from target.")
        except Exception as e:
            logger.error(f"Error with replace field method. Could not get and remove field from target record. Error: {e}")
        
    # Add copy field to target record.
    try:
        target_record.add_ordered_field(field)
        return target_record
    except Exception as e:
        logger.error(f"Error adding copy field to target record. Error: {e}")
        return "Error"

def replace_field(target_record, source_record, field):
    """Replaces a field in one record with the value from another.

    Args:
        target_record (pymarc record object): record requiring updating.
        source_record (pymarc record object): record containing data to be merged
                                              into target.
        field (str | pymarc Field object): Marc field tag for example "100", 
                            or Field object that can use inbuilt tag.

    Returns:
        pymarc record object: target record with or without updates.
    """
    copy_field = get_field_from_source(source_record, field)
    

    if copy_field is not None:
        target_record = add_field_to_target(target_record, copy_field)
        
    updated_target_record = fix_655_gmgpc(target_record)
    return updated_target_record
    

def fix_655_gmgpc(record):
    fields = record.get_fields('655')

    for field in fields:
        if len(field.get_subfields('2')) > 0:
            field['2'] = 'gmgpc' if field['2'].startswith('gmgpc') \
                else field['2'] # strips out trailing punctuation/whitespace in $2
            value = field['a'] if field['2'] == 'gmgpc' else ""

            if value.endswith("."): # only updates gmgpc with final period
                field['a'] = value[0:-1]
    
    return record

def is_parent(record):
    fields = record.get_fields('956')
    for field in fields:
        if field['b'] == "PARENT":
            return True
    return False

def record_to_mrc(record, output_filename):
    """Write xml record to mrc file.
    
    Args:
        record (pymarc Record object)
        output_filename (str): path and filename for output mrc file.

    Processing:
        XML is translated into MARC binary and appended to desired file.
    """
    with open(output_filename, 'ab') as out:
        out.write(record.as_marc())
    out.close()

