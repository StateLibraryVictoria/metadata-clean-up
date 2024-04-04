from logger_config import *
import os
import subprocess

debug_log_config("marcedit-functions")
logger = logging.getLogger()

try:
    CMARCEDIT_PATH = os.getenv("CMARCEDIT_PATH")
except KeyError:
    print("Missing configuration. Location of cmarcedit.exe must be added to environment variables.")
try:
    RULES = os.getenv("MARCEDIT_RULES")
except KeyError:
    print("Missing configuration. Location of MarcEdit rules file must be added to environment variables.")
#TASK = os.getenv("MARCEDIT_TASK") ## Not yet working.


# The following works the same as MarcBreaker. Could be useful if a mrk file is preferred.
def break_marc_record(record_path,output_name):
    """Breaks Marc records into mrk for MarcEdit.

    Args:
        record_path (str) | path to mrc record including extension.
        output_name (str) | filename for output including .mrk extension. Will automatically place in output directory.
    """
    subprocess.run(CMARCEDIT_PATH + f" -s {record_path} -d output\\{output_name} -break", shell=True)


# Won't run without the rules file, which needs to be properly escaped.
# Output is the same as it prints to the user screen, so may require work to parse to something machine readable.
def validate_mrc_record(record_path):
    """Runs MarcEdit validation via command line over file.

    Args:
        record_path: str | Path to file requiring validation, can be .mrc or .mrk.
        CMARCEDIT_PATH: str | Path to local cmarcedit.exe must be included in env file.
        RULES: str | Path to local rules file for MarcEdit must be included in env file.
    """
    subprocess.run(CMARCEDIT_PATH + f" -s {record_path} -d output\\report.txt -validate -rules {RULES}", shell=True)

# Run tasks - NOT WORKING. writes an empty file. Terminal shows garbled text. It appears to have found the task
#subprocess.run(CMARCEDIT_PATH + f" -s {final_path} -d output\\tast_2_applied.mrc -task {task} -experimental", shell=True)

