import pymarc
import os
import re
import logging
from copy import deepcopy
import re
from src.logger_config import *

logger = logging.getLogger(__name__)
debug_log_config("log_file")
logger.info("==XML load and process log==")

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
    if tag.startswith("1"):
        match_fields = source_record.get_fields('100','110','111','130')
    else:
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

def subfield_is_in_record(record, query, tag, subfield, whitespace=True):
    """Returns matching subfield from a record matching either exact or with whitespace stripped.

        Args:
        record: (pymarc Record object)
        query: (str) - value expected in field
        tag: (str)
    """
    # check record is Record
    if not isinstance(record, pymarc.record.Record):
        raise Exception("Record must be a pymarc Record object.")
    
    # get the matched accession numbers
    for item in record.get_fields(tag):
        if item[subfield] == query:
            return query
        elif item[subfield].replace(" ","") == query.replace(" ",""):
            return item[subfield]
        else:
            continue
    
    # log failed records and return None
    for item in record.get_fields(tag):
        try:
            logger.info(f"No match found for {query} in {tag} ${subfield} in record {record['001'].value()}. Record has 037: {item}")
        except Exception as e:
                print(f"error adding log for failed query search {e}")
    return None

def get_nonfiling_characters(string):
    nonfiling = "^(\W?)(the |an |a |le |l')?\s*"
    query = re.search(nonfiling, string)
    return query.group()

def fix_245_indicators(record):
    """Checks aspects of the 245 in a record and updates indicators"""
    wr = deepcopy(record)
    # First indicator - 0 - No added entry, 1 - Added entry (no 1xx)
    title = wr.title
    title = title.lower()

    # fix first indicator
    if len(wr.get_fields('100', '110', '111', '130')) == 0:
        first_indicator = '1'
    else:
        first_indicator = '0'
    # If second indicator is not numeric, get nonfiling and calculate length.
    valid_ind2 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    current_ind2 = wr['245'].indicator2
    if current_ind2 not in valid_ind2:
        prefix_store = get_nonfiling_characters(title)
        if prefix_store is not None:
            second_indicator = str(len(prefix_store))
        else:
            second_indicator = '0'
    else:
        second_indicator = wr['245'].indicator2

    for field in wr.get_fields('245'):
        field.indicator1 = first_indicator
        field.indicator2 = second_indicator
    wr.remove_fields('245')
    wr.add_ordered_field(field)
    return wr

# Fix 773-ind1 : 0 - Display note, 1 - Do not display note
def fix_830_ind2(record):
    # Check if record has 830.
    fix_830 = record.get_fields('830')
    if len(fix_830) == 0:
        return record
    # Process existing 830s
    wr = deepcopy(record)
    wr.remove_fields('830')
    valid_ind2 = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    for field in fix_830:
        if field.indicator2 not in valid_ind2:
            try:
                title = field['a']
                field.indicator2 = str(len(get_nonfiling_characters(title.lower())))
                wr.add_ordered_field(field)
            except Exception as e:
                print(f"Error getting subfield $a from 830: {e}")
                logger.error(f"Error for record {wr['001'].value()} getting subfield $a from 830: {e}")
    return record
            
def fix_773_ind1(record):
    fix_730 = record.get_fields('773')
    if len(fix_730) == 0:
        return record
    wr = deepcopy(record)
    wr.remove_fields('773')
    for field in fix_730:
        if field.indicator1 not in ['0', '1']:
            field.indicator1 = '0'
        wr.add_ordered_field(field)
    return wr
    
def fix_1xx_ind2(record):
    xx1 = record.get_fields('100', '110', '111', '130')
    if len(xx1) == 0:
        return record
    wr = deepcopy(record)
    wr.remove_fields('100', '110', '111', '130')
    for field in xx1:
        field.indicator2 = "\\"
        wr.add_ordered_field(field)
    return wr

