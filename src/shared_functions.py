import os
import re
import pymarc
import json
import pandas as pd
from src.api_call import *
from src.xml_load_and_process import *
from src.transform_marc_file import *


logger = logging.getLogger()


def setup_logger(
    name,
    log_file,
    formatter=logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
    level=logging.INFO,
):
    """Generates multiple loggers for a single script"""

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def setup_directories():
    """Initialises directories"""
    log_path = os.path.join("logs")
    json_path = os.path.join("json")
    input_path = os.path.join("input", "load")
    processed_path = os.path.join("output", "record_processing", "processed")
    exception_path = os.path.join("output", "record_processing", "exceptions")
    output_path_mrc = os.path.join("output", "mrc", "split")
    output_path_mrc_merge = os.path.join("output", "mrc", "merge")
    input_path_mrc = os.path.join(input_path, "mrc")
    output_path_xml = os.path.join("output", "xml")
    parent_records_path = os.path.join(output_path_mrc, "parent")
    many_records_path = os.path.join(output_path_mrc, "many")
    paths = [
        log_path,
        input_path,
        processed_path,
        exception_path,
        output_path_mrc,
        input_path_mrc,
        output_path_xml,
        parent_records_path,
        many_records_path,
        output_path_mrc_merge,
        json_path,
    ]

    for path in paths:
        if not os.path.exists(path):
            # create missing directories
            os.makedirs(path)

    # create logfile location
    open(os.path.join(log_path, "log_file.log"), "a")


def clear_temporary_files():
    """Removes temporary files from specific directories once complete."""
    print("Cleaning temporary working directories...")
    output_path_mrc = os.path.join("output", "mrc", "split")
    output_path_mrc_merge = os.path.join("output", "mrc", "merge")
    json_path = os.path.join("json")
    paths = [json_path, output_path_mrc, output_path_mrc_merge]

    for local_path in paths:
        if os.path.exists(local_path):
            count = 0
            for root, dir, files in os.walk(local_path):
                # remove files
                file_list = [os.path.join(root, file) for file in files]
                for item in file_list:
                    try:
                        os.remove(item)
                        count += 1
                        logger.debug(f"Removed {item}")
                    except Exception as e:
                        print(f"Error removing files: {e}")
        print(f"Removed {count} files from {local_path}")
        logger.info(f"Removed {count} files from {local_path}")


def get_callable_files(dir_name):
    """Get a list of filepaths in target directory"""
    output_list = []
    logger.info(f"Searching directory {dir_name} for callable files.")
    try:
        for root, dirs, files in os.walk(dir_name):
            files.sort()
            output_list = [os.path.join(dir_name, file) for file in files]
        return output_list
    except Exception as e:
        logger.error(f"Error getting callable files: {e}")


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
            'parent_many_dict': parent ids as keys for many records matching the same record.
    """
    identifiers = {
        "parent_records": [],
        "many_records": [],
        "parent_ids": [],
        "parent_many_dict": {},
    }
    with open(input_filename, "rb") as fh:
        reader = pymarc.MARCReader(fh)  # creates
        for record in reader:
            id = record.get_fields("001")[0].value()
            if is_parent(record):
                identifiers["parent_records"].append(id)
                output_file = os.path.join(
                    "output", "mrc", "split", "parent", f"record_{id}.mrc"
                )
            else:
                identifiers["many_records"].append(id)
                field_950 = record.get_fields("950")
                if len(field_950) > 0:
                    for field in field_950:
                        if field.get("p") is not None:
                            p_id = record["950"]["p"]
                            existing_manys = identifiers["parent_many_dict"].get(p_id)
                            if existing_manys is not None:
                                new_list = existing_manys + [id]
                                identifiers["parent_many_dict"].update({p_id: new_list})
                            else:
                                identifiers["parent_many_dict"].update({p_id: [id]})
                    try:
                        identifiers["parent_many_dict"].update({})
                        if record["950"]["p"] not in identifiers["parent_ids"]:
                            identifiers["parent_ids"].append(record["950"]["p"])
                    except KeyError:
                        logger.info("950 p not present in record.")
                output_file = os.path.join(
                    "output", "mrc", "split", "many", f"record_{id}.mrc"
                )
            with open(output_file, "wb") as f:
                f.write(record.as_marc())
    print(identifiers["parent_many_dict"])
    return identifiers


def get_missing_records(existing_records, request_ids, output_directory):
    """Call API process to add missing parent records to existing file.

    Args:
        existing_records: list (str) - identifiers for already downloaded records.
        request_ids: list (str) - identifiers required for download (may overlap with existing)
        output_file: str - MARC file with filepath to write retrieved records to.

    Processing:
        Checks request_ids not in existing_records. Prepares and calls API to retrieve missing records.
        Writes them to file.
    """
    logger.debug(f"Number of existing records: {len(existing_records)}")
    logger.debug(f"Number of request ids: {len(request_ids)}")

    # Check what identifiers need to be retrieved.
    missing_list = []
    for identifier in request_ids:
        if identifier not in existing_records:
            missing_list.append(identifier)

    # Retrieve records.
    logger.info("Missing list:")
    logger.info(missing_list)

    required = chunk_identifiers(missing_list)
    xml = "<collection>"  # Wraps xml in root element collection
    if check_api_key():
        for key in required:
            response = get_bibs(key, required[key])
            data = response.json()
            string = json.dumps(data, indent=4)
            bibs = json.loads(string)
            for item in bibs["bib"]:
                for key in item:
                    if key == "anies":
                        value = item["anies"][0].replace(
                            '<?xml version="1.0" encoding="UTF-16"?>', ""
                        )
                        xml += value
    xml += "</collection>"  # Closes root element wrapping.
    with open(
        "output//xml//records_retrieved.xml",
        "w",
        encoding="utf-8",
        errors="backslashreplace",
    ) as out:
        out.write(xml)

    # Load xml to pymarc Record object array.
    record_array = pymarc.parse_xml_to_array("output//xml//records_retrieved.xml")

    # Write to mrc.
    for record in record_array:
        id = record.get_fields("001")[0].value()
        output_file = os.path.join(output_directory, f"record_{id}.mrc")
        with open(output_file, "wb") as mrc_out:
            mrc_out.write(record.as_marc())


# Load records as dataframe
def get_identifiers_from_spreadsheet(filename):
    """Loads a spreadsheet to dataframe from filename and sets mms id columns to
    have prefix mms_id.

    Returns the dataframe with columns containing MMS ids prefixed with "mms_id_".
    Columns with mms_id prefix that do not contain MMS Ids will have the prefix
    'ex_' added.
    If there are no mms id columns identified, will exit program.
    """
    try:
        data = pd.read_excel(filename)
    except Exception as e:
        print(f"Error opening file: {e}")
        logger.error(f"Error loading spreadsheet: {e}")
    column_titles = list(data)
    # convert all values to string
    data[column_titles] = data[column_titles].astype(str)
    # get mms_id columns
    current_column = []
    for title in column_titles:
        if any(data[title].str.startswith("99")) and any(
            data[title].str.endswith("7636")
        ):
            current_column.append(title)
            column_titles.remove(title)
    if len(current_column) == 0:
        print("No mms ids identified. Quitting.")
        logger.info("No MMS Ids identified in supplied spreadsheet.")
        sys.exit()
    column_dict = {}
    for title in column_titles:
        if title.startswith("mms_id"):
            new_title = f"ex_{title}"
            column_dict.update({title: new_title})
    for column in current_column:
        if not column.startswith("mms_id"):
            column_dict.update({column: f"mms_id_{column}"})
    data = data.rename(columns=column_dict)
    return data


def merge_marc_records(directory, output_filename):
    try:
        for root, dir, files in os.walk(directory):
            dir_list = [os.path.join(directory, file) for file in files]
            dir_list.sort()
    except Exception as e:
        logger.error(f"Error getting directory list for marc record merge: {e}")
    logger.debug(f"Directory list: {dir_list}")
    try:
        with open(output_filename, "ab") as output:
            for file in dir_list:
                with open(file, "rb") as mrc:
                    reader = pymarc.MARCReader(mrc)
                    for record in reader:
                        output.write(record.as_marc())
    except Exception as e:
        logger.error(f"Error merging MARC records: {e}")
    return None


def get_list_error_ids(validator_report):
    identifiers = []
    mms_id = r"99\d+7636"
    with open(validator_report, "r") as report:
        data = report.read()
        identifiers = re.findall(mms_id, data)
    logger.info(f"Number of records with errors identified: {len(identifiers)}")
    return identifiers


def output_file_with_validation(
    source_record_path, output_directory, output_filename=None, merged=False
):
    """Creates merged MARC file in output directory with MarcEdit validation report and MARC Text File (.mrk).

    Args:
    source_record_path (str / path) - location of files to be added to output.
    output_directory (str / path) - output location.
    output_filename (str) - output filename. If this is not set, will prompt user for
                    input in terminal.
    merged (bool) - Default to False which runs merge processing, but can be
                    set to True to run on files that have already been merged

    Processing:
    Adds '.mrc' extension to filename if not already present.
    Merges multiple records in source path into one MARC file.
    Saves to output directory.
    Runs cmarkedit.exe on file to create a validation report and a .mrk file.

    """
    if output_filename is None:
        print("Enter filename for merged MARC file.")
        merge_filename = input()
    else:
        merge_filename = output_filename
    if not merge_filename.endswith(".mrc"):
        merge_filename, ext = os.path.splitext(merge_filename)
        merge_filename = merge_filename + ".mrc"
    merge_output = os.path.join(output_directory, merge_filename)
    print(merge_output)

    if not merged:
        try:
            merge_marc_records(source_record_path, merge_output)
            print(f"File has been created at: {merge_output}")
            logger.info(f"File has been created at: {merge_output}")
        except Exception as e:
            print(f"Merge failed: {e}")
            logger.info(f"Merge failed: {e}")
    try:
        print("output filename: " + merge_output.replace(".mrc", ".mrk"))
        break_marc_record(merge_output, merge_output.replace(".mrc", ".mrk"))
        print("MARK Text file (.mrk) created.")
    except Exception as e:
        print(f"Generation of .mrk file failed: {e}")
    try:
        validation_filename = merge_output.replace(".mrc", "_validation.txt")
        validate_mrc_record(merge_output, validation_filename)
    except Exception as e:
        print(f"Validation of merged records failed: {e}")


def list_files(directory):
    file_list = os.listdir(directory)

    if len(file_list) == 0:
        print("No files in load directory. Stage file and try again.")
        sys.exit()

    print("\n===CHECKING STAGED FILES===\n")

    for file in file_list:
        print("Staged file found: " + file)
        logger.info("Staged file: " + file)

    print("Do you wish to process all files? y/n")
    response = input()
    if not response.lower().startswith("y"):
        print("Ending program. Please re-stage files and resubmit.")
        logger.info("User ended program.")
        sys.exit()
    print("")
    return file_list


def get_ids_from_file(directory, file_list):
    """Get ids from file"""
    id_list = []
    for file in file_list:
        if ".xls" in file:
            data = get_identifiers_from_spreadsheet(os.path.join(directory, file))
            for column in data.columns:
                if column.startswith("mms_id"):
                    ids = data[column].to_list()
                    id_list.extend(ids)
                    print(
                        f"MMS_ids found: {len(ids)} ids added to list from file {file}."
                    )
                    logger.info(
                        f"MMS_ids found: {len(ids)} ids added to list from file {file}."
                    )
        else:
            with open(os.path.join(directory, file), "r") as f:
                ids = re.findall("99\d+7636", f.read())
                id_list.extend(ids)
                print(f"MMS_ids found: {len(ids)} ids added to list from file {file}.")
                logger.info(
                    f"MMS_ids found: {len(ids)} ids added to list from file {file}."
                )
    return id_list
