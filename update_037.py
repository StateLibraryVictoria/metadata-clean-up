import os
from copy import deepcopy
from sys import exit
from copy import deepcopy
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.logger_config import *
from src.transform_marc_file import *
from src.api_call import *


logger = logging.getLogger(__name__)
debug_log_config("log_file")

# Debugging flag - set to True to work with existing records or False to start from scratch.
downloaded_records = False

# Setup workspace
setup_directories()
ROOT_DIR = os.path.abspath(os.curdir)

# Set directories
output_dir_many = os.path.join("output", "mrc", "split", "many")
output_dir_parent = os.path.join("output", "mrc", "split", "parent")
merge_path = os.path.join("output","mrc","merge")
# Set final output files
valid_output = os.path.join(merge_path, "updated_records.mrc")
invalid_output = os.path.join(merge_path, "records_with_exceptions.mrc")

# cleanup directories for temporary files
if downloaded_records:
    print("Not clearing directory, working with downloaded records.")
else:
    clear_temporary_files()

# Load identifiers and accession numbers from spreadsheet
filename = "acc_no_no_dupes_filtered_index3_acc_endswith2or4.xlsx"
location = os.path.join(ROOT_DIR,"input","load","excel", filename)
df = get_identifiers_from_spreadsheet(location)
headers = list(df)
logger.info(f"Loaded dataframe of shape {df.shape}")

# Get list of mms ids from dataframe
identifiers = []
for head in headers:
    if head.startswith("mms_id"):
        expected = df[head].tolist()
        identifiers.extend(expected)

# Get MARC record from API
if downloaded_records:
    print("Not calling API, working with downloaded records.")
else:
    if check_api_key():
        try:
            get_missing_records([], identifiers, output_dir_many)
        except Exception as e:
            print(f"Error retrieving bibs: {e}")
            logger.error(f"Error retrieving bibs: {e}")


# Get PARENT records from API
record_files = get_callable_files(output_dir_many)
parent_id_dict = iterate_get_parents(record_files)
parent_df = pd.DataFrame.from_dict(parent_id_dict, orient="index", columns=['mms_id', 'parent_id'])
parent_cols = list(parent_df)
parent_df[parent_cols] = parent_df[parent_cols].astype(str)
parent_df.mms_id = parent_df.mms_id.str.strip()

# Create list of ids for API request
unique_parents = parent_df.parent_id.unique().tolist()


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


# Add parent ids to df
df_join = pd.merge(df.assign(mms_id=df.mms_id.astype(str)), 
                   parent_df.assign(mms_id=parent_df.mms_id.astype(str)), 
                   how='left', on='mms_id')
# Create columns containing filenames
df_join['filename'] = output_dir_many + os.sep + ("record_" + df_join['mms_id'] + ".mrc")
df_join['parent_file'] = output_dir_parent + os.sep + ("record_" + df_join['parent_id']+".mrc")

"""Processing records"""

# Create valid 037
identifier_subfield = pymarc.Subfield(code='a', value='identifier')
field_037 = pymarc.Field(
    tag = '037',
    indicators = ["",""],
    subfields = [
        identifier_subfield,
        pymarc.Subfield(code='b', value='State Library of Victoria')
    ]
)

# exception tracking variables
counter = 0 # successful matches
list_match = []
exceptions = 0 # unsuccessful matches
list_not_match = []
list_has_037 = []
match_parent = False

# Iterates through rows in dataframe to process files
for index, row in df_join.iterrows():
    try:
        # Get 037 from parent record if it matches file_label.
        with open(row['parent_file'], 'rb') as pf:
            p_reader = pymarc.MARCReader(pf)
            for record in p_reader:
                parent_rec = deepcopy(record)
                # Gets matching accession number from parent record or returns None
                new_label = subfield_is_in_record(record, row['file_label'], '037', 'a')
                if new_label is not None:
                    df_join['file_label'].replace(row['file_label'], new_label, inplace=True)
                    match_parent = True
                    counter += 1
                else:
                    list_not_match.append((row['mms_id'], row['file_label']))
                    with open(invalid_output, 'ab') as output:
                        output.write(parent_rec.as_marc()) # writes parent record to invalid_output file for QA.
                    logger.info(f"Record written to exceptions file: {invalid_output}")
    except Exception as e:
        print(f"Error getting parent 037 using subfield_is_in_record method for record {row}. Error: {e}")
    try:
        if match_parent:
            with open(row['filename'], 'rb') as fh:
                reader = pymarc.MARCReader(fh)
                for record in reader:
                    fix_record = deepcopy(record)
                    # Cleanup record to replace common fields, fix indicator encoding, etc.
                    fix_record = big_bang_replace(fix_record, parent_rec)
                    fix_record = fix_indicators(fix_record)
                    fix_record = fix_655_gmgpc(fix_record)
                    try: 
                        # Check for existing 037 and add exception if it exists.
                        if len(record.get_fields('037')) > 0:
                            for identifier in record.get_fields('037'):
                                list_has_037.append((row['mms_id'], row['file_label'], identifier))
                                logger.info(f"Record {row['mms_id']} has existing 037: {identifier}. Will not apply file label {row['file_label']}")
                                with open(invalid_output, 'ab') as output:
                                    output.write(parent_rec.as_marc())
                                    output.write(fix_record.as_marc())
                                logger.info(f"Record written to exceptions file: {invalid_output}")
                        else:
                            identifier_subfield = pymarc.Subfield(code='a', value=new_label)
                            field_037 = pymarc.Field(
                                tag = '037',
                                indicators = ["\\","\\"],
                                subfields = [
                                identifier_subfield,
                                pymarc.Subfield(code='b', value='State Library of Victoria')
                                ]
                            )
                            fix_record.add_ordered_field(field_037)
                            list_match.append(row['mms_id'])
                            with open(valid_output, 'ab') as output:
                                output.write(fix_record.as_marc())
                    except Exception as e:
                        logger.error(f"Error adding 037 to record {row['mms_id']}. Error: {e}")
        else: # cleanup and handling for records that don't match parent.
            logger.info(f"Record {row['mms_id']} accession number {row['file_label']} not in parent record {row['parent_id']}")
            with open(row['filename'], 'rb') as fh:
                logger.debug(f"Checking record {row['mms_id']} which failed check against parent record doesn't have existing 037.")
                reader = pymarc.MARCReader(fh)
                for record in reader:
                    fix_record = deepcopy(record)
                    # Cleanup record to replace common fields, fix indicator encoding, etc.
                    fix_record = big_bang_replace(fix_record, parent_rec)
                    fix_record = fix_indicators(fix_record)
                    fix_record = fix_655_gmgpc(fix_record)
                    # Write record to exceptions file.
                    with open(invalid_output, 'ab') as output:
                            output.write(fix_record.as_marc())
                    try: # Check if record already has 037.
                        existing_037 = fix_record.get_fields('037')
                        if len(existing_037) > 0:
                            for field in existing_037:
                                logger.info(f"Record {row['mms_id']} did not match identifier in parent record" + 
                                            f" also has existing 037 fields.Contains field: {field}")
                        else:
                            logger.debug("Record doesn't have existing 037.")
                    except Exception as e:
                        logger.error(f"Error checking for existing 037 in record {row['mms_id']}.")
                    logger.info(f"Record {row['mms_id']} written to exceptions file: {invalid_output}")
    except Exception as e:
        print(f"Error opening file from pandas df: {e}")
        logger.error(f"Error opening file from pandas df: {e}")

# Checks for items added to both valid and invalid lists
for item in list_match:
    if item in list_not_match:
        print("Item in both lists:")
        print(item)
        logger.warning(f"Item written to both exceptions and valid files: {item}")

# Print out errors for the operator to handle.
logger.info("Summary of exceptions")
for id, acc in list_not_match:
    print(f"Failed accession record match for {id} with file label: {acc}")
    logger.info(f"Failed accession record match for {id} with file label: {acc}")
for id, acc, exi in list_has_037:
    print(f"Existing 037 present in record {id} -- Current 037: {exi} -- File label: {acc}")
    logger.info(f"Existing 037 present in record {id} -- Current 037: {exi} -- File label: {acc}")

# Validate and return how many records failed.
if os.path.isfile(valid_output):
    valid_path, valid_name = os.path.split(valid_output)
    output_file_with_validation(valid_output, valid_path, output_filename=valid_name, merged=True)
else:
    print("No valid records written to file.")

# check file exists
if os.path.isfile(invalid_output):
    invalid_path, invalid_name = os.path.split(invalid_output)
    output_file_with_validation(invalid_output, invalid_path, output_filename=invalid_name, merged=True)
else:
    print("No exceptions written to file.")