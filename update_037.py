import os
from sys import exit
from copy import deepcopy
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.logger_config import *



logger = logging.getLogger(__name__)
debug_log_config("log_file")


# Setup workspace
setup_directories()

# Load identifiers and accession numbers from spreadsheet

# Get MARC record from API

# Get PARENT records from API

# Create validation file of all records

# Run validation on records

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