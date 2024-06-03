import os
import re
import time
from copy import deepcopy
from sys import exit
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.transform_marc_file import *
from src.api_call import *

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def setup_logger(name, log_file, level=logging.INFO):
    """To setup as many loggers as you want"""

    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger


def normalise_title(input):
    input = input.lower()
    output = re.sub("\W", "", input)
    return output


timestr = time.strftime("%Y%m%d-%H%M%S")
logger_name = f"logs/update_037_{timestr}.log"
logger = setup_logger(None, logger_name, level=logging.INFO)
logger_2 = setup_logger(
    "name_collision_logger", "logs/name_mismatch_950l.log", level=logging.DEBUG
)
print("Root log file created with name: " + logger_name)

# Debugging flag - set to True to work with existing records or False to start from scratch.
downloaded_records = False
print(
    "Unless you choose to work with downloaded records, all output and temporary files will be deleted."
)
print("Work with downloaded records? (y/n)")
response = input()
if response.lower().startswith("y"):
    downloaded_records = True

# Setup workspace
setup_directories()

KEY = os.getenv("KEY")
if KEY is None:
    print("API Key is None. Exiting.")
    sys.exit()
ROOT_DIR = os.path.abspath(os.curdir)

# Set directories
output_dir_many = os.path.join("output", "mrc", "split", "many")
output_dir_parent = os.path.join("output", "mrc", "split", "parent")
merge_path = os.path.join("output", "mrc", "merge")
# Set final output files
valid_output = os.path.join(merge_path, "updated_records.mrc")
invalid_output = os.path.join(merge_path, "failed_update_records.mrc")
other_exceptions = os.path.join(merge_path, "other_exceptions.mrc")

# cleanup directories for temporary files
if downloaded_records:
    print("Not clearing directory, working with downloaded records.")
else:
    clear_temporary_files()

# Load identifiers and accession numbers from spreadsheet
files = list_files(os.path.join(ROOT_DIR, "input", "load", "excel"))
filename = files[0]
logger.info("Processing file: " + filename)
location = os.path.join(ROOT_DIR, "input", "load", "excel", filename)
df = get_identifiers_from_spreadsheet(location)
headers = list(df)
logger.info(f"Loaded dataframe of shape {df.shape}")


# Get MARC record from API
if downloaded_records:
    print("Not calling API, working with downloaded records.")
else:
    # Get list of mms ids from dataframe
    identifiers = []
    for head in headers:
        if head.startswith("mms_id"):
            expected = df[head].tolist()
            identifiers.extend(expected)

    if len(identifiers) > 0:
        if check_api_key():
            try:
                get_missing_records([], identifiers, output_dir_many)
            except Exception as e:
                print(f"Error retrieving bibs: {e}")
                logger.error(f"Error retrieving bibs: {e}")


# Get PARENT records from API
record_files = get_callable_files(output_dir_many)
parent_id_dict = get_id_dictionary(record_files)
logger.info(parent_id_dict)

# Create list of ids for API request
unique_parents = list(parent_id_dict.keys())

# get parents via Alma API
if downloaded_records:
    print("Not calling API, working with downloaded records.")
else:
    if check_api_key():
        try:
            get_missing_records([], unique_parents, output_dir_parent)
        except Exception as e:
            print(f"Error retrieving bibs: {e}")
            logger.error(f"Error retrieving bibs: {e}")


# Create columns containing filenames
df["filename"] = output_dir_many + os.sep + ("record_" + df["mms_id"] + ".mrc")

"""Processing records"""

# Create valid 037
identifier_subfield = pymarc.Subfield(code="a", value="identifier")
field_037 = pymarc.Field(
    tag="037",
    indicators=["", ""],
    subfields=[
        identifier_subfield,
        pymarc.Subfield(code="b", value="State Library of Victoria"),
    ],
)

# exception tracking variables
counter = 0  # successful matches
list_match = []
exceptions = 0  # unsuccessful matches
list_not_match = []
list_has_037 = []
list_name_not_match = []

list_already_present = []

# Iterate through parent dictionary
for key in unique_parents:
    if key.startswith("99"):
        parent_filename = f"record_{key}.mrc"
        with open(os.path.join(output_dir_parent, parent_filename), "rb") as pf:
            p_reader = pymarc.MARCReader(pf)
            for parent_rec in p_reader:
                parent_written = False
                try:
                    p_title = normalise_title(parent_rec.title)
                except Exception as e:
                    p_title = None
                manys = parent_id_dict.get(key)
                for many in manys:
                    has_exception = False
                    match_parent = False
                    filename = f"record_{many}.mrc"
                    # Get the file label from the dataframe
                    file_label = df.loc[df["mms_id"] == many, "file_label"].values[0]
                    new_label = subfield_is_in_record(
                        parent_rec, file_label, "037", "a"
                    )
                    if new_label is None:
                        parent_accession = parent_rec.get_fields("037")
                        if len(parent_accession) == 0:
                            first_record = "No 037"
                        else:
                            first_record = parent_accession[0].get("a")
                        logger.info(
                            f"File label match failed - MANY: {many}, "
                            f"file_label: {file_label}, "
                            f"parent_id: {parent_rec['001'].value()}, "
                            f"num_037: {len(parent_accession)}, "
                            f"data: {first_record}"
                        )
                    else:
                        match_parent = True
                    with open(os.path.join(output_dir_many, filename), "rb") as fh:
                        reader = pymarc.MARCReader(fh)
                        for record in reader:
                            try:
                                w_title = normalise_title(record["950"]["l"])
                                if p_title is not None and w_title != p_title:
                                    if record["245"]["a"] not in list_name_not_match:
                                        list_name_not_match.append(record["950"]["l"])
                                        logger_2.debug(
                                            f"Failed title match: MANY 950$l {record['950']['l']} PARENT {parent_rec['245']['a']}"
                                        )
                            except Exception as e:
                                w_title = None

                            wr = deepcopy(record)
                            try:
                                fix_record = many_record_cleanup(wr, parent_rec)
                                has_exception = check_fields(
                                    fix_record,
                                    ("100", "110", "111", "130"),
                                    ("700", "710", "711", "720", "730"),
                                )
                            except Exception as e:
                                has_exception = True
                                logger.error(
                                    f"Error while cleaning MANY record {str(many)} : {e}"
                                )
                            if match_parent:
                                # check for existing 037
                                if len(record.get_fields("037")) > 0:
                                    for identifier in record.get_fields("037"):
                                        if identifier.get("a") == new_label:
                                            list_already_present.append(
                                                (many, file_label, identifier)
                                            )
                                        list_has_037.append(
                                            (
                                                record["001"].value(),
                                                file_label,
                                                identifier,
                                            )
                                        )
                                        logger.info(
                                            f"Record {record['001'].value()} has existing 037: {identifier}. Will not apply file label {file_label}"
                                        )
                                        has_exception = True
                                else:
                                    identifier_subfield = pymarc.Subfield(
                                        code="a", value=new_label.upper()
                                    )
                                    field_037 = pymarc.Field(
                                        tag="037",
                                        indicators=["\\", "\\"],
                                        subfields=[
                                            identifier_subfield,
                                            pymarc.Subfield(
                                                code="b",
                                                value="State Library of Victoria",
                                            ),
                                        ],
                                    )
                                    fix_record.add_ordered_field(field_037)
                                    list_match.append(
                                        (
                                            record["001"].value(),
                                            file_label,
                                            parent_rec["001"].value(),
                                        )
                                    )
                            else:
                                list_not_match.append(
                                    (
                                        record["001"].value(),
                                        file_label,
                                        parent_rec["001"].value(),
                                    )
                                )
                            if has_exception:
                                output_file = other_exceptions
                            elif match_parent:
                                output_file = valid_output
                                parent_written = True
                            else:
                                output_file = invalid_output
                            with open(output_file, "ab") as output:
                                if not parent_written:
                                    output.write(parent_rec.as_marc())
                                    parent_written = True
                                output.write(fix_record.as_marc())

# Checks for items added to both valid and invalid lists
for item in list_match:
    if item in list_not_match:
        print("Item in both lists:")
        print(item)
        logger.warning(f"Item written to both exceptions and valid files: {item}")

# Print out errors for the operator to handle.
logger.info("Summary of exceptions")
print(list_not_match)
for id, acc, p_mmsid in list_not_match:
    print(f"Failed accession record match for {id} with file label: {acc}")
    logger.info(f"Failed accession record match for {id} with file label: {acc}")
for id, acc, exi in list_has_037:
    logger.info(
        f"Existing 037 present in record {id} -- Current 037: {exi} -- File label: {acc}"
    )
logger.warning(
    "Existing correct 037: "
    + str(len(list_already_present))
    + " records already had correct 037 in record."
)
for id, acc, exi in list_already_present:
    logger.debug(
        f"Existing 037 matched record {id} -- Current 037: {exi} -- File label: {acc}"
    )

# Validate and return how many records failed.
if os.path.isfile(valid_output):
    valid_path, valid_name = os.path.split(valid_output)
    output_file_with_validation(
        valid_output, valid_path, output_filename=valid_name, merged=True
    )
else:
    print("No valid records written to file.")

# check file exists
if os.path.isfile(invalid_output):
    invalid_path, invalid_name = os.path.split(invalid_output)
    output_file_with_validation(
        invalid_output, invalid_path, output_filename=invalid_name, merged=True
    )
else:
    print("No failed matches written to file.")

# check file exists
if os.path.isfile(other_exceptions):
    other_path, other_name = os.path.split(other_exceptions)
    output_file_with_validation(
        other_exceptions, other_path, output_filename=other_name, merged=True
    )
else:
    print("No other exceptions written to file.")

# Build archive file of unmodified MANY records.
output_dir_many
output_file_with_validation(
    output_dir_many, merge_path, output_filename="unedited_many_backup.mrc"
)
