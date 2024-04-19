import pymarc
import os
import re
import logging
from copy import deepcopy
import re
from src.logger_config import *

logger = logging.getLogger(__name__)
debug_log_config("log_file")


def get_fields_from_source(source_record, field):
    """Checks for field in source record and returns list of fields with 1xx handling.

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
        amount = f"no {tag} fields" if len(source_record.get_fields(tag)) < 1 else f"too many {tag} fields"
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
        
    return target_record
    

def fix_655_gmgpc(record):
    """Fixes trailing punctuation from 655 with $2 gmgpc subject headings."""
    fields = record.get_fields('655')

    for field in fields:
        if len(field.get_subfields('2')) > 0:
            field['2'] = 'gmgpc' if field['2'].startswith('gmgpc') \
                else field['2'] # strips out trailing punctuation/whitespace in $2
            value = field['a'] if field['2'] == 'gmgpc' else ""

            if not value.endswith("."): # adds final period to gmgpc if required.
                field['a'] = value + "."
    
    return record

def is_parent(record):
    """Returns True if 956$b == PARENT"""
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
        # 037 case for ranged identifiers
        elif tag == '037' and "-" in item[subfield]:
            identifiers = enumerate_037(item[subfield])
            for id in identifiers:
                if id == query or id.replace(" ","") == query.replace(" ",""):
                    return id
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
    # \W catches anything that returns False for str.isalnum()
    # Unicode characters in other scripts inherit the Alphabetic property
    # and return True if Alphabetic.
    nonfiling = r"^(\W?)(the |an |a |le |l')?\s*"
    query = re.search(nonfiling, string.lower())
    return query.group()

def fix_245_indicators(record):
    """Checks aspects of the 245 in a record and updates indicators"""
    wr = deepcopy(record)
    title = wr.title

    # fix first indicator - 0 - No added entry, 1 - Added entry (no 1xx)
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

def fix_indicators(record):
    """Applies fixes for 1xx-ind2, 245-ind1, 245-ind2, 773-ind1, 830-ind2.
    """
    wr = deepcopy(record)
    wr = fix_1xx_ind2(wr)
    wr = fix_245_indicators(wr)
    wr = fix_773_ind1(wr)
    wr = fix_830_ind2(wr)
    return wr

def make_suffix_list(start, end, text_part=""):
    """
    args:
        start (int) : Numeric start of id range
        end (int) : Numeric end of id range.
        text_part (str) : Identifier prefix, eg PHO. If none, defaults to ""
    """
    output = []
    for item in range(start, end+1):
        if text_part is not None:
            id = text_part + str(item)
        else:
            id = str(item)
        output.append(id)
    return output

def enumerate_037(id_range):
    """Function for taking id range and returning a list of all identifiers. 
    Currently works for identifiers with / character before range and - in range.
    eg. H83.12/1-5, MS12345/1/PHO234-235. If the id cannot be enumerated returns input in a list.
    Does not handle alphabetic suffixes (eg. H2012.12/1a-c)"""
    # if doesn't contain "-" return value as item in list.
    if "-" not in id_range or "/" not in id_range:
        return [id_range]
    
    # check that range doesn't end with letter
    if not id_range[-1].isnumeric():
        return [id_range]

    # whole part case (eg. "H2012.200/248 - H2012.200/251")
    id_range_stripped = id_range.replace(" ","")
    part1, part2 = id_range_stripped.split("-")
    if "/" in part1 and "/" in part2:
        root1 = part1[0:part1.rfind("/")]
        root2 = part2[0:part2.rfind("/")]
        if root1 == root2:
            id_root = root1
            id_range_stripped = id_root + "/" + part1[part1.rfind("/")+1:] + "-" + part2[part2.rfind("/")+1:]
        
        

    # else, split by last index of /
    id_root, id_suffix = id_range_stripped[0:id_range_stripped.rfind("/")], id_range_stripped[id_range_stripped.rfind("/")+1:]
    end_part = id_suffix.split("-")

    # declare variables
    text_part_end = None
    text_part_start = None

    if "." in id_suffix: # RWP has this style
        first_prefix = None
        first_suffix = None
        second_prefix = None
        second_suffix = None
        if "." in end_part[0]:
            first_prefix, first_suffix = end_part[0].split(".")
        else:
            first_suffix = end_part[0]
        if "." in end_part[1]:
            second_prefix, second_suffix = end_part[1].split(".")
        else:
            second_suffix = end_part[1]
        if first_prefix and first_suffix:
            if first_suffix.isnumeric():
                start = int(first_suffix)
                text_part_start = first_prefix
            else:
                return [id_range]
        elif first_suffix:
            if first_suffix.isnumeric():
                start = int(first_suffix)
            else:
                return [id_range]
        if second_prefix and second_suffix:
            if second_suffix.isnumeric():
                end = int(second_suffix)
                text_part_start = second_prefix
            else:
                return [id_range]
        elif second_suffix:
            if second_suffix.isnumeric():
                end = int(second_suffix)
            else:
                return [id_range]
            
        # check if the text part is the same between both bits
        if text_part_start is not None and text_part_end is not None:
            if text_part_start == text_part_end:
                text_part = text_part_start + "."
            else:
                logger.info(f"Identifier range: {id_range} has conflicting start and end prefixes.")
                return [id_range]
        elif text_part_start is not None:
            text_part = text_part_start + "."
        elif text_part_end is not None:
            return [id_range]
        
        # finalise the . output version.
        suffixes = make_suffix_list(start, end, text_part)
        output = []
        for item in suffixes:
            identifier = id_root + r"/" + item
            output.append(identifier)
        output.sort()
        return output
        
    # MS and H identifiers
    try:
        first = end_part[0]
    except IndexError:
        return [id_range]
    if not first.isnumeric():
        text_part = re.sub("\d+\.?","",first)
        num_part = re.sub("\D+", "", first)
        start = int(num_part)
        if text_part is not None:
            if first.startswith(text_part):
                prefix = True
            else:
                suffix = True
    else:
        start = int(first)
        text_part = None

    # Second part
    try:
        second = end_part[1]
    except IndexError:
        return [id_range]
    if not second.isnumeric():
        text_part_second = re.sub("\d+","",second)
        num_part = re.sub("\D+\.?", "", second)
        start = int(num_part)
        if text_part:
            if not text_part == text_part_second:
                return [id_range] # something weird if this happens
        else: 
            text_part = text_part_second
        if second.startswith(text_part):
            prefix = True
        else:
            suffix = True
        end = int(num_part)
    else:
        end = int(second)

    final_range = make_suffix_list(start, end, text_part)

    # count through output to get final
    output = []
    for item in final_range:
        id = id_root + r"/" + item
        output.append(id)
    output.sort()
    return output