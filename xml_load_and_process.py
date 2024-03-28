import pymarc
import os
import logging
import re
from logger_config import *

debug_log_config("load-xml")
logger = logging.getLogger()


def get_marc_tag(pymarc_record, field, subfield):
    """Retrieve value in specified field.

    Args:
        pymarc_record: Pymarc Record Object.
        field: str - MARC tag, eg '001', '500', etc.
        subfield: str - Subfield tag eg. 'a', '4'.
    """
    try:
        value = pymarc_record[field][subfield]
        return value
    except:
        logger.debug(f"Error getting field {field} ${subfield}")
        return None




def load_pymarc_record(filename):
    """Load XML record as pymarc record object.
    
    If 1 record in the array, returns record object. 
    Otherwise prints warning and returns record array.
    """
    record = pymarc.parse_xml_to_array(filename)
    if len(record) == 1:
        return record[0]
    else:
        print("Multi-record file identified.")
        return record




def get_callable_files(dir_name):
    """Get a list of filepaths in target directory"""
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


def get_fields_from_source(source_record, field):
    """Checks for field in source record and returns list of fields.

    Args:
        source_record (pymarc Record object): record containing data with target field.
        field (str | pymarc Field object): field desired to be copied.

    Returns:
        List of pymarc Field objects
    """
    if type(field) == str:
        tag = field
    else:
        tag = field.tag

    # Check that field in source record.
    match_fields = source_record.get_fields(tag)
    if len(match_fields) == 0:
        amount = f"no {tag} fields" if get_field_count(source_record, tag) < 1 else f"too many {tag} fields"
        logger.warning(f"Source record contains {amount}. "
                        + "Cancelling operation.")
        return None
    else:
        logger.info(f"Source record contains {len(match_fields)} copies of field {tag}. "
                        + "Continuing operation")
    return match_fields


def remove_field_from_target(target_record, tag):
    """Removes all copies of a field by tag. Removes all 1xx fields when a 100, 110, 111, 130 supplied."""
    try: # try to remove the fields from the record to be updated
        if tag.startswith("1"):
            target_1xx = target_record.get_fields('100', '110', '111', '130')
            logger.info(f"Removing {len(target_1xx)} subfields from record.")
            print(f"Removing {len(target_1xx)} subfields from record.")
            if len(target_1xx) > 1:
                print("Multiple 1xx fields removed. See log for details.")
                logger.warn("Multiple 1xx fields removed. All fields have been removed.")
            for f in target_1xx:
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
        return target_record
    except Exception as e:
        logger.error(f"Error with replace field method. Could not get and remove field from target record. Error: {e}")


def add_field_to_target(target_record, fields, replace=True):
    """ Returns the target record with the passed subfield. Default strips existing instances of field.

    Args:
        target_record: pymarc Record object - record requiring updating.
        field: list (pymarc Field object) - list of fields to be added to record.
        replace: bool - whether to keep or delete existing fields. Defaults to delete existing copies of record (True).

    Returns:
        pymarc Record object: transformed record.
    """
    notRepeatable = ["010","018","036","038","040","042","044","045","066","100","110","111","130","240","243","245","254", "256", "263", "306","357","507","514"]


    # Check that only one of non-repeatable fields are in supplied fields.
    tag_list = []
    for match_field in fields:
        tag_list += match_field.tag
        tag_list.sort()
    for tag in tag_list:
        if tag in notRepeatable:
            if tag_list.count(tag) > 1:
                print(f"Source record has multiple copies of unrepeatable field {tag}. Skipping record.")
                logger.error(f"Source record has multiple copies of unrepeatable field {tag}. Skipping record.")
                return target_record
    
    logger.info("Processing record: " + target_record.get_fields('001')[0].value())

    # remove existing fields
    if replace:
        for field in fields:
            target_record = remove_field_from_target(target_record, field.tag)
    else: # removes non repeatable fields from target record
        for field in fields:
            if field.tag in notRepeatable:
                target_record = remove_field_from_target(target_record, field.tag)
        
        
    # Add copy field to target record.
    for field in fields:
        try:
            target_record.add_ordered_field(field)
        except Exception as e:
            logger.error(f"Error adding copy fields to target record. Error: {e}")
            return None
    return target_record

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
    copy_fields = get_fields_from_source(source_record, field)
    

    if copy_fields is not None:
        target_record = add_field_to_target(target_record, copy_fields)
        
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

