import pytest
import shutil
import os

# Set the project root to resolve source file.
ROOT_DIR = os.path.abspath(os.curdir)

# Path variables
filename = "test_file_with_errors.mrc"
single_p_record = "record_9933644453607636.mrc"
test_marc_file = os.path.join(ROOT_DIR, "tests","test_data","marc_data","test_file_with_errors.mrc")
test_parents = os.path.join(ROOT_DIR, "tests","test_data","marc_data", "parent")
missing_records = ["9938846603607636"]

# Create MARC file
@pytest.fixture(scope="session")
def temp_marc_file(tmp_path_factory):
    """Returns the filename and path of a MARC file
    copied from test_data to the temporary directory
    for use across tests.
    """
    mrcfn = tmp_path_factory.getbasetemp() / filename
    shutil.copyfile(test_marc_file, mrcfn)
    yield mrcfn

# Create required directory structure in temp directory
@pytest.fixture(scope="session")
def setup_working_directory(tmp_path_factory):
    """Returns a path to the temporary directory where 
    folder structure has been generated.

    Used for other tests.
    """
    location = tmp_path_factory.getbasetemp()
    os.chdir(location)
    log_path = os.path.join("logs")
    input_path = os.path.join("input","load")
    processed_path = os.path.join("output", "record_processing","processed")
    exception_path = os.path.join("output", "record_processing","exceptions")
    output_path_mrc = os.path.join("output", "mrc","split")
    input_path_mrc = os.path.join(input_path, "mrc")
    output_path_xml = os.path.join("output","xml")
    parent_records_path = os.path.join(output_path_mrc,"parent")
    many_records_path = os.path.join(output_path_mrc,"many")
    paths = [log_path, input_path, processed_path, exception_path, output_path_mrc, 
             input_path_mrc, output_path_xml, parent_records_path, many_records_path]
    
    for path in paths:
        if not os.path.exists(path):
            # create missing directories
            os.makedirs(path)
    yield location

# Create copy of required match records in output directory.
@pytest.fixture(scope="session")
def missing_parents(tmp_path_factory):
    """Returns output directory containing expected MARC files
    copied from test_data to temporary directory for testing.
    """
    location = tmp_path_factory.getbasetemp()
    output_dir = os.path.join("output", "mrc", "split", "parent")
    output = os.path.join(location, output_dir)
    os.chdir(location)
    try:
        copydir = output
        shutil.copytree(test_parents, copydir, dirs_exist_ok=True)
    except Exception as e:
        print(f"Error occured copying parents in test: {e}")   
    output = os.path.join(location, output_dir)
    yield output