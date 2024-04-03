import pytest
import os
import time
from shared_functions import *

"""Tests for shared functions.

Data for this section is defined in conftest.py.
"""

# Test setup_directories()
def test_setup_directories(setup_working_directory):
    local = setup_working_directory
    os.chdir(local)
    assert os.path.exists("logs")
    assert os.path.exists(os.path.join("output","xml"))
    assert os.path.exists(os.path.join("output","mrc","split","many"))

# Test split_marc_records()
def test_split_marc_records_dictionary_keys_generated(temp_marc_file):
    location = os.path.dirname(temp_marc_file)
    os.chdir(location)
    setup_directories()
    dictionary = split_marc_records(temp_marc_file)
    time.sleep(1)
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
def test_get_missing_records_gets_17_files(missing_parents):
    location = missing_parents
    print(location)
    for root, dir, files in os.walk(location):
        assert len(files) == 17
