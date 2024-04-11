import os
from src.shared_functions import *

"""Tests for shared functions.

Data for this section is defined in conftest.py.
"""

# Setup test data
def load_test_files(filename):
    data = open(os.path.join(filename), 'r', encoding="utf-8", errors='backslashreplace')
    return data.read()

ROOT_DIR = os.path.abspath(os.curdir)

## Type should be input or expected
def create_file_array(test_data, type):
    input_path = os.path.join(test_data, type)
    for root, dir, files in os.walk(input_path):
        files.sort()
        output_list = [path.join(input_path, file) for file in files]
    return output_list

data_path = path.join(ROOT_DIR,"tests","test_data","xml_load_and_process")
input_path = os.path.join(data_path,'input')

## input files
input_files = create_file_array(data_path, "input")
korean_example = input_files[0]
chinese_example = input_files[1]
photo_example_01 = input_files[2]
photo_example_02 = input_files[3]

source_path = os.path.join(data_path, "source", "source_record.xml")
source_record = load_test_files(source_path)


# Test setup_directories()
def test_setup_directories(setup_working_directory):
    local = setup_working_directory
    os.chdir(local)
    assert os.path.exists("logs")
    assert os.path.exists(os.path.join("output","xml"))
    assert os.path.exists(os.path.join("output","mrc","split","many"))

# get_callable_files
def test_get_callable_files():
    files = get_callable_files(input_path)
    expected = [path.join(input_path, "example_01_korean_rare.xml"), 
                path.join(input_path, "example_02_chinese_rare.xml"), 
                path.join(input_path, "example_03_photo_child.xml"), 
                path.join(input_path, "example_04_photo_child.xml")]
    assert files == expected

# Test split_marc_records()
def test_split_marc_records_dictionary_keys_generated(temp_marc_file):
    location = os.path.dirname(temp_marc_file)
    os.chdir(location)
    setup_directories()
    dictionary = split_marc_records(temp_marc_file)
    assert "many_records" in dictionary
    assert "parent_records" in dictionary
    assert "parent_ids" in dictionary

def test_split_marc_records_dictionary_values_generated(temp_marc_file):
    location = os.path.dirname(temp_marc_file)
    os.chdir(location)
    setup_directories()
    dictionary = split_marc_records(temp_marc_file)
    assert len(dictionary['many_records']) == 17
    assert len(dictionary["parent_records"]) == 0
    assert len(dictionary["parent_ids"]) == 17

def test_split_marc_records_files_generated_many_dir(temp_marc_file):
    location = os.path.dirname(temp_marc_file)
    os.chdir(location)
    setup_directories()
    split_marc_records(temp_marc_file)
    for root, dir, files in os.walk(os.path.join("output","mrc","split","many")):
        assert len(files) == 17
        
# Test get_missing_records()
def test_split_marc_records_equals_expected(missing_parents, temp_marc_file):
    location = missing_parents
    identifiers = split_marc_records(temp_marc_file)
    expected_ids = identifiers["parent_ids"]
    # modify the expected ids to match filenames
    expected_ids[:] = ["".join(("record_",id,".mrc")) for id in expected_ids]
    expected_ids.sort()
    for root, dir, files in os.walk(location):
        files.sort()
        assert files == expected_ids

# Test merge_marc_records(directory, output_filename)

# Test get_identifiers_from_spreadsheet(filename):

# Test get_list_error_ids(validator_report)
def test_get_list_error_ids(get_validation_report):
    ids = get_list_error_ids(get_validation_report)
    assert len(ids) == 386
    assert "9939647904007636" in ids
    assert "9939662982307636" in ids