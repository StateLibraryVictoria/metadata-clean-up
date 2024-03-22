from shared_functions import *
from xml_load_and_process import *
from get_parent_ids import *
import pymarc
import os

debug_log_config("test")
logger = logging.getLogger()

input_path = os.path.join("input","load", "mrc")
output_path = os.path.join("output", "mrc", "records_fixed_gmgpc.mrc")

# returns file extension for single file in input directory.
for root, dir, files in os.walk(input_path):
    output_list = [os.path.join(input_path, file) for file in files]
    if len(output_list) == 0:
        print("No files in input directory. Add files to /input/load/mrc.")
    elif len(output_list) > 1:
        print(f"Too many files in input directry. Only stage one file. Directory contains {len(output_list)} files.")
    else:
        filename, extension = os.path.splitext(output_list[0])
        logger.info(f"Input directory contains {filename} with extension {extension}")
        filepath = output_list[0]

output_file = open(output_path, 'ab')

with open(filepath, 'rb') as fh:
    reader = pymarc.MARCReader(fh)
    for record in reader:
        fields = record.get_fields('655')
        fix_655_gmgpc(record)
        output_file.write(record.as_marc())



