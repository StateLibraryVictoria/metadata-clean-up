from os import path
from copy import deepcopy
import pymarc
from src.api_call import validate_mmsid
from src.shared_functions import get_callable_files
from src.xml_load_and_process import *

logger = logging.getLogger()


def many_record_cleanup(many_record, parent_record):
    """Runs all current cleanup actions on many record."""
    if not isinstance(many_record, pymarc.record.Record):
        raise Exception(
            f"Record to be updated must be a pymarc Record object. Object supplied is: {type(many_record)}, value {many_record}"
        )
    if not isinstance(parent_record, pymarc.record.Record):
        logger.error(
            f"Error completing big bang replace. Parent record must be a pymarc Record object. Many record: {many_record['001'].value()}"
        )
        return many_record
    fix_record = deepcopy(many_record)
    fix_record = big_bang_replace(fix_record, parent_record)
    fix_record = fix_indicators(fix_record)
    fix_record = fix_655_gmgpc(fix_record)
    return fix_record


def big_bang_replace(many_record, parent_record):
    """Replaces fields based on the big bang cleanup project.
    Fields 1xx, 260/264, 6xx, 7xx, 8xx are copied from parent to many record."""
    if not isinstance(many_record, pymarc.record.Record):
        raise Exception(
            f"Record to be updated must be a pymarc Record object. Object supplied is: {type(many_record)}, value {many_record}"
        )
    if not isinstance(parent_record, pymarc.record.Record):
        logger.error(
            f"Error completing big bang replace. Parent record must be a pymarc Record object. Many record: {many_record['001'].value()}"
        )
        return many_record
    fix_record = deepcopy(many_record)
    onexx = ["100", "110", "111", "130"]
    pub_year = ["260", "264"]
    subjects = [
        "600",
        "610",
        "611",
        "630",
        "648",
        "650",
        "651",
        "653",
        "654",
        "655",
        "656",
        "657",
        "658",
        "662",
        "690",
        "691",
        "696",
        "697",
        "698",
        "699",
    ]
    added_entries = [
        "700",
        "710",
        "711",
        "720",
        "730",
        "740",
        "752",
        "753",
        "754",
        "790",
        "791",
        "792",
        "793",
        "796",
        "797",
        "798",
        "799",
    ]
    series = ["800", "810", "811", "830"]
    notRepeatable = [
        "010",
        "018",
        "036",
        "038",
        "040",
        "042",
        "044",
        "045",
        "066",
        "100",
        "110",
        "111",
        "130",
        "240",
        "243",
        "245",
        "254",
        "256",
        "263",
        "306",
        "357",
        "507",
        "514",
    ]
    replace_list = [onexx, pub_year, subjects, added_entries, series]

    # Checks for 246 without indicators and adds 246 to iterable if exists.
    replace_246 = False
    alt_title = ["246"]
    if len(many_record.get_fields("246")) > 0:
        fields = many_record.get_fields("246")
        check_fields = [
            1 for field in fields if field.indicator1 == " " and field.indicator2 == " "
        ]
        if sum(check_fields) == len(fields):
            replace_246 = True

    if replace_246:
        fix_record.remove_fields("246")
        replace_list.append(alt_title)

    # Update fields from parent record
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
        print(
            f"Error setting up list of present fields in parent for big bang replace: {e}"
        )
    try:  # remove records
        for item in in_parent:
            if item.startswith("1"):
                for tag in onexx:
                    fix_record.remove_fields(tag)
            if item.startswith("2"):
                for tag in pub_year:
                    fix_record.remove_fields(tag)
            elif item.startswith("6"):
                for tag in subjects:
                    fix_record.remove_fields(tag)
            elif item.startswith("7"):
                for tag in added_entries:
                    fix_record.remove_fields(tag)
            elif item.startswith("8"):
                for tag in series:
                    fix_record.remove_fields(tag)
    except Exception as e:
        print(f"Error removing fields in many record: {e}")
    try:
        for item in in_parent:
            for field in parent_record.get_fields(item):
                fix_record.add_ordered_field(field)
    except Exception as e:
        print(f"Error adding fields to many record {e}")
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
        id = pymarc_record["950"]["p"]
    except KeyError:
        return None
    if validate_mmsid(id):
        return id
    else:
        logger.debug(f"Invalid MMS id: {id}")
        return None


def iterate_get_parents(
    filepath_list, parent_only=False
):  # also get child MMS Id and append as a tuple.
    """Get a dictionary or list of ids. parents_only=True will return a list of parent ids. Otherwise returns a dictionary with {key: (MANY, PARENT)}
    Args:
        filepath_list (list) : .mrc or .xml filepath list from get_callable_files.
        parent_only (bool) : Default to False. Set to True to return only parent ids as list.

    Processing: Loads records with Pymarc.
        Gets 001
        Gets the parent MMS ID if present.
        Adds values to a dictionary with MMS Id of record as key.
    Output: Dictionary with a index: [id, parent_id]
    """

    if filepath_list == None or len(filepath_list) == 0:
        logger.info("Iterate get parents failed as filepath list is empty.")
        return None
    index = 0
    filepath_list.sort()
    records_without_parents = False
    if filepath_list[0].endswith(".mrc"):
        try:
            parent_id_list = []
            parent_id_dict = {}
            for file in filepath_list:
                with open(file, "rb") as fh:
                    reader = pymarc.MARCReader(fh)
                    for record in reader:
                        try:
                            if record["956"]["b"] == "MANY":
                                id = record["001"].value()
                                parent_id = get_parent_id(record)
                                logger.debug(f"Record id: {id}, parent_id {parent_id}")
                                if parent_id is not None:
                                    parent_id_list.append(parent_id)
                                    parent_id_dict.update({index: [id, parent_id]})
                                    index += 1
                                else:  # checks record is not a Parent and if so
                                    logger.info(
                                        f"Missing parent id: Many record {id} did not contain Parent id in 950$p"
                                    )
                                    records_without_parents = True
                            else:
                                logger.info(
                                    f"Not MANY record: Record {record['001'].value()} is not a MANY record."
                                )
                        except KeyError:
                            logger.info(f"No 956$b: Record {id} did not contain 956$b")
                            records_without_parents = True
        except Exception as e:
            logger.error(f"Error reading marc from iterating parent ids: {e}")
    elif filepath_list[0].endswith(".xml"):
        try:
            parent_id_dict = {}
            for file in filepath_list:
                records = pymarc.parse_xml_to_array(file)
                for record in records:
                    id = record["001"].value()
                    parent_id = get_parent_id(record)
                    if parent_id is not None:
                        parent_id_dict.update({index: [id, parent_id]})
                        index += 1
        except Exception as e:
            logger.error(
                f"Error iterating parent ids: {e} "
                + " 950 $p may be invalid or not present in some records."
            )
    else:
        print("No valid files supplied. Files must be .mrc or .xml.")
        logger.error("No valid files supplied. Files must be .mrc or .xml.")
    if records_without_parents:
        print(
            "Processing completed with exceptions. Some files did not contain parents. See logfile for a list of MMS Ids."
        )
    if parent_only:
        return parent_id_list
    else:
        return parent_id_dict


def format_ids_for_api(id_list):
    """
    Input: list of ids.
    Processing: Concatinates them to csv
    Output: String
    """
    try:
        string = ",".join(id_list)
        return string
    except Exception as e:
        logger.error(f"Error adding items to string: {e}")


def write_ids_to_list(id_string, output_directory, filename):
    """
    Input: List of MMS Ids, output directory, filename
    Processing: Writes parent mms ids to list callable by the API function.
    Output: File with mms ids separated by commas.
    """
    try:
        output_location = path.join(output_directory, filename)
        with open(output_location, "w", encoding="utf-8") as output_file:
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
