import os
from logger_config import *

debug_log_config("shared-functions")
logger = logging.getLogger()

processed_path = os.path.join("output", "record_processing","processed")
exception_path = os.path.join("output", "record_processing","exceptions")

def write_file_to_exceptions(file, error, open=True):
    """Called to create a file in the exceptions area when a call fails.

    Args:
        file (str | file object): If file is str it must be a directory and open must be set to False.
        error (Exception): Pass exceptions from the previous step through to the exception handler.
        open (bool): Status of the file True equals open, False equals string. Default is True.

    Processing:
        Gets filename and writes to exceptions directory while also logging steps to logfile.

    Returns:
        None | Writes output to file and log.
    """
    if open==False:
        try:
            file = open(file, "r", encoding="utf-8", errors="backslashreplace")
            data = file.read()
        except Exception as e:
            logger.error(f"Exception identified with file {file}. Error: {e}")
    else:
        try:
            if file.readable():
                data = file.read()
            else:
                data = file
        except Exception as e:
            logger.error(f"Exception identified with file. Error: {e}")
    
    filename = os.path.basename(file.name)
    logger.info(f"Exception identified with file {filename}.")

    output_file = open(os.path.join(exception_path, filename), "a", encoding="utf-8", errors='backslashreplace')

    if error:
        output_file.write(repr(error)) # Write exception type and error to string.
        logger.info(f"Error message written to file {filename}.")
    output_file.write(data)
    logger.info(f"File with exceptions {filename} written to to /output/record_processing/exceptions.")




def write_file_to_processed(file, open=True):
    if open==False:
        try:
            file = open(file, "r", encoding="utf-8", errors="backslashreplace")
            data = file.read()
        except Exception as e:
            write_file_to_exceptions(file, e, open=False)
            logger.error("Error encountered during write_file_to_processed with unopened file.")
    else:
        try:
            if file.readable():
                data = file.read()
            else:
                data = file
        except Exception as e:
            write_file_to_exceptions(file, e)
            logger.error("Error encountered during write_file_to_processed with opened file.")
    
    filename = os.path.basename(file.name)
    output_file = open(os.path.join(processed_path, filename), "a", encoding="utf-8", errors='backslashreplace')
    output_file.write(data)
    logger.debug(f"File written to /output/record_processing/processed with filename {filename}")