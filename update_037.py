import os
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
print(len(identifiers))
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
"""try:
    get_missing_records([], parent_ids, output_dir)
except Exception as e:
    print(f"Error retrieving bibs: {e}")
    logger.error(f"Error retrieving bibs: {e}")"""

# Create validation file of all records
merge_path = os.path.join("output","mrc","merge")
many_validation_report = os.path.join("output","many_records_report.txt")
parent_validation_report = os.path.join("output","merged_parent_validation_file.mrc")
many_merge_name = os.path.join(merge_path, many_validation_report)
parent_merge_name = os.path.join(merge_path, parent_validation_report)
#merge_marc_records(output_dir_many, many_merge_name)
#merge_marc_records(output_dir_parent, parent_merge_name)

# Run validation on records
#validate_mrc_record(many_merge_name, "many_records_report.txt")
#validate_mrc_record(parent_merge_name,"parent_record_report.txt")

many_errors = get_list_error_ids(many_validation_report)
df['filename'] = "record_" + df['mms_id'] + ".mrc"
df['validation_error'] = df['mms_id'].isin(many_errors)
# Had to do this extra coding in merge as it wasn't able to join on mms_id even when 
# both were showing as type object and set using astype(str)
df_join = pd.merge(df.assign(mms_id=df.mms_id.astype(str)), 
                   parent_df.assign(mms_id=parent_df.mms_id.astype(str)), 
                   how='left', on='mms_id')
print(df_join.filename.head())
print(df_join.shape)
valid = df_join.loc[~df_join.validation_error]
invalid = df_join.loc[df_join.validation_error]
print(valid.head())
print(valid.shape)
print(invalid.head())
print(invalid.shape)

# Processing for valid records

# Processing for invalid records

"""This group is filtered from Description Original Material accession numbers. Records in this category are believed to have the lowest risk of duplication or exceptions.

Count of records: 1448  
Accession number types: H, MS, LT, YLT  

Processing plan:  

Use API to retrieve MMS Ids from list.
For each MMS Id in list, query and retireve parent MMS Id.
Run validation on MANY records

Perform checks (failures should be added to exceptions file for further investigation)  
- The accession number is on the parent record. [RAISE NOT ON PARENT]
- The parent record doesn't have a version of the accession number with a further subdivision. [RAISE SUBDIVIDED]
- Titles are the same (ignoring brackets). [RAISE DIFFERENT TITLE]
- The parent 520 / 505 doesn't reference the identifier specifically.
    - if it does, can we copy that data into the child?
- There are 540 and 542 fields in the record.
- 655 has $2
- 655 fix trailing period on gmgpc
- Other checks, 260/264/008, 245/100, """