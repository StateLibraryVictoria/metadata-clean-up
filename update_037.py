import os
from copy import deepcopy
from sys import exit
from copy import deepcopy
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.logger_config import *
from src.transform_marc_file import *



logger = logging.getLogger(__name__)
debug_log_config("log_file")


# Setup workspace
setup_directories()
ROOT_DIR = os.path.abspath(os.curdir)

# Load identifiers and accession numbers from spreadsheet
filename = "acc-minus-duplicates-csv_unique_root.xlsx"
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
output_dir_many = os.path.join("output", "mrc", "split", "many")
"""
try:
    get_missing_records([], identifiers, output_dir)
except Exception as e:
    print(f"Error retrieving bibs: {e}")
    logger.error(f"Error retrieving bibs: {e}")
"""

# Get PARENT records from API
many_mrc_files = os.path.join(ROOT_DIR,"output","mrc","split","many")
record_files = get_callable_files(many_mrc_files)
parent_ids = iterate_get_parents(record_files)
parent_df = pd.DataFrame.from_dict(parent_ids, orient="index", columns=['mms_id', 'parent_id'])
parent_cols = list(parent_df)
parent_df[parent_cols] = parent_df[parent_cols].astype(str)
parent_df.mms_id = parent_df.mms_id.str.strip()
output_dir_parent = os.path.join("output", "mrc", "split", "parent")
"""
try:
    get_missing_records([], parent_ids, output_dir)
except Exception as e:
    print(f"Error retrieving bibs: {e}")
    logger.error(f"Error retrieving bibs: {e}")
"""

# Create validation file of all records
merge_path = os.path.join("output","mrc","merge")
many_validation_report = os.path.join("output","many_records_report.txt")
parent_validation_report = os.path.join("output","merged_parent_validation_file.mrc")
many_merge_name = os.path.join(merge_path, many_validation_report)
parent_merge_name = os.path.join(merge_path, parent_validation_report)
"""
merge_marc_records(output_dir_many, many_merge_name)
merge_marc_records(output_dir_parent, parent_merge_name)
"""

# Run validation on records
"""
validate_mrc_record(many_merge_name, "many_records_report.txt")
validate_mrc_record(parent_merge_name,"parent_record_report.txt")
"""

many_errors = get_list_error_ids(many_validation_report)
df['validation_error'] = df['mms_id'].isin(many_errors)
# Had to do this extra coding in merge as it wasn't able to join on mms_id even when 
# both were showing as type object and set using astype(str)
df_join = pd.merge(df.assign(mms_id=df.mms_id.astype(str)), 
                   parent_df.assign(mms_id=parent_df.mms_id.astype(str)), 
                   how='left', on='mms_id')
df_join['filename'] = output_dir_many + os.sep + ("record_" + df_join['mms_id'] + ".mrc")
df_join['parent_file'] = output_dir_parent + os.sep + ("record_" + df_join['parent_id']+".mrc")
valid = df_join.loc[~df_join.validation_error]
invalid = df_join.loc[df_join.validation_error]

# Processing for valid records
    # 037 process
"""identifier_subfield = pymarc.Subfield(code='a', value='identifier')
field_037 = pymarc.Field(
    tag = '037',
    indicators = ["",""],
    subfields = [
        identifier_subfield,
        pymarc.Subfield(code='b', value='State Library of Victoria')
    ]
)"""
    # 655 process

# Processing for invalid records
    # 037 process
    # 655 process
    # 260/264
    # field duplication

# all of them
# For each row in the df:
    # Open the file.
    # Open the parent file.
    # Turn file label into 037
    # Check if parent contains identifcal 037
        # If no - log and output to mismatch file.
        # Else: add 037 to many record.
    # Fix 655
counter = 0
exceptions = 0
list_not_match = []
list_match = []
list_has_037 = []
target_df = df_join
valid_output = os.path.join(merge_path, "updated_records.mrc")
invalid_output = os.path.join(merge_path, "records_with_exceptions.mrc")
replace_fields = ['100', '110', '111', '260', '264','830','655']
for index, row in target_df.iterrows():
    try:
        match_parent = False
        # Get 037 from parent record if it matches file_label.
        with open(row['parent_file'], 'rb') as pf:
            p_reader = pymarc.MARCReader(pf)
            for record in p_reader:
                parent_rec = deepcopy(record)
                new_label = subfield_is_in_record(record, row['file_label'], '037', 'a')
                if new_label is not None:
                    target_df['file_label'].replace(row['file_label'], new_label, inplace=True)
                    match_parent = True
                    counter += 1
                else:
                    list_not_match.append((row['mms_id'], row['file_label']))
                    with open(invalid_output, 'ab') as output:
                        output.write(record.as_marc())
                    logger.info(f"Record written to exceptions file: {invalid_output}")
    except Exception as e:
        print(f"Error getting parent 037 using subfield_is_in_record method {e}")
    try: # Processing target record
        if match_parent:
            with open(row['filename'], 'rb') as fh:
                reader = pymarc.MARCReader(fh)
                for record in reader:
                    fix_record = deepcopy(record)
                    fix_record = big_bang_replace(fix_record, parent_rec)
                    fix_record = fix_indicators(fix_record)
                    fix_record = fix_655_gmgpc(fix_record)
                    try: 
                        # Check no existing 037
                        if len(record.get_fields('037')) > 0:
                            for identifier in record.get_fields('037'):
                                list_has_037.append((row['mms_id'], row['file_label'], identifier))
                                logger.info(f"Record {row['mms_id']} has existing 037: {identifier}. Will not apply file label {row['file_label']}")
                                with open(invalid_output, 'ab') as output:
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
        else:
            logger.info(f"Record {row['mms_id']} accession number {row['file_label']} not in parent record {row['parent_id']}")
            with open(row['filename'], 'rb') as fh:
                logger.debug(f"Checking record {row['mms_id']} which failed check against parent record doesn't have existing 037.")
                reader = pymarc.MARCReader(fh)
                for record in reader:
                    fix_record = deepcopy(record)
                    fix_record = big_bang_replace(fix_record, parent_rec)
                    fix_record = fix_indicators(fix_record)
                    fix_record = fix_655_gmgpc(fix_record)
                    with open(invalid_output, 'ab') as output:
                            output.write(fix_record.as_marc())
                    try:
                        existing_037 = fix_record.get_fields('037')
                        if len(existing_037) > 0:
                            for field in existing_037:
                                logger.info(f"Record {row['mms_id']} did not match identifier in parent record" + 
                                            f" also has existing 037 fields.Contains field: {field}")
                        else:
                            logger.debug("Record doesn't have existing 037")
                    except Exception as e:
                        logger.error(f"Error checking for existing 037 in record {row['mms_id']}.")
                    logger.info(f"Record {row['mms_id']} written to exceptions file: {invalid_output}")
    except Exception as e:
        print(f"Error opening file from pandas df: {e}")
        logger.error(f"Error opening file from pandas df: {e}")
for item in list_match:
    if item in list_not_match:
        print("Item in both lists:")
        print(item)
        print("End")

# Print out errors for the operator to handle.
logger.info("Summary of exceptions")
for id, acc in list_not_match:
    print(f"Failed accession record match for {id} with file label: {acc}")
    logger.info(f"Failed accession record match for {id} with file label: {acc}")
for id, acc, exi in list_has_037:
    print(f"Existing 037 present in record {id} -- Current 037: {exi} -- File label: {acc}")
    logger.info(f"Existing 037 present in record {id} -- Current 037: {exi} -- File label: {acc}")

# Validate and return how many records failed.
valid_path, valid_name = os.path.split(valid_output)
output_file_with_validation(valid_path, valid_path, filename=valid_name, merged=True)
invalid_path, invalid_name = os.path.split(invalid_output)
output_file_with_validation(invalid_path, invalid_path, filename=invalid_name, merged=True)