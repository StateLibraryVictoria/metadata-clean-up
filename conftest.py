import pytest
import shutil
import os
from shared_functions import *

# Set the project root to resolve source file.
ROOT_DIR = os.path.abspath(os.curdir)

# Path variables
filename = "test_file_with_errors.mrc"
test_marc_file = os.path.join(ROOT_DIR, "tests","test_data","marc_data","test_file_with_errors.mrc")
missing_records = ["9938846603607636"]

# Create MARC file
@pytest.fixture(scope="session")
def temp_marc_file(tmp_path_factory):
    mrcfn = tmp_path_factory.getbasetemp() / filename
    shutil.copyfile(test_marc_file, mrcfn)
    yield mrcfn

# Create required directory structure in temp directory
@pytest.fixture(scope="session")
def setup_working_directory(tmp_path_factory):
    location = tmp_path_factory.getbasetemp()
    os.chdir(location)
    setup_directories()
    yield location

# Get missing parents for marc file
@pytest.fixture(scope="session")
def missing_parents(tmp_path_factory):
    location = tmp_path_factory.getbasetemp()
    os.chdir(location)
    identifiers = split_marc_records(test_marc_file)
    output_dir = os.path.join("output", "mrc", "split", "parent")
    get_missing_records(identifiers["parent_records"], identifiers["parent_ids"], output_dir)
    output = os.path.join(location, output_dir)
    yield output