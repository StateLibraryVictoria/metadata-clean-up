from os import path
import pytest

from xml_load_and_process import *

# Setup test data
def load_test_files(filename):
    data = open(os.path.join(filename), 'r', encoding="utf-8", errors='backslashreplace')
    return data.read()

## Type should be input or expected
def create_file_array(test_data, type):
    input_path = os.path.join(test_data, type)
    for root, dir, files in os.walk(input_path):
        output_list = [path.join(input_path, file) for file in files]
    return output_list

data_path = path.join("tests","test_data","xml_load_and_process")

## input files
input_files = create_file_array(data_path, "input")
korean_example = input_files[0]
chinese_example = input_files[1]
photo_example_01 = input_files[2]
photo_example_02 = input_files[3]


# get_marc_tag
@pytest.mark.parametrize("input_file, expected", 
                         [
                             (input_files[0], "Gosŭt'ŭ ch'aildŭ ="), 
                             (input_files[1], "Qing chun wu qi tu xing ="), 
                             (input_files[2], "Swan Hill Pioneer Settlement"), 
                             (input_files[3], "Ken Done's house")
                             ])
def test_get_marc_tag_245a(input_file, expected):
    record = load_pymarc_record(input_file)
    title = get_marc_tag(record, "245", "a")
    assert title == expected

@pytest.mark.parametrize("input_file, expected", 
                         [
                             (input_files[0], "223 pages :"), 
                             (input_files[1], "250 pages ;"), 
                             (input_files[2], "1 digital file"), 
                             (input_files[3], "1 digital file")
                             ])
def test_get_marc_tag_300a(input_file, expected):
    record = load_pymarc_record(input_file)
    title = get_marc_tag(record, "300", "a")
    assert title == expected

# load_pymarc_record
@pytest.mark.parametrize("input_file, expected", 
                          [
                             (input_files[0], "Gosŭt'ŭ ch'aildŭ ="), 
                             (input_files[1], "Qing chun wu qi tu xing ="), 
                             (input_files[2], "Swan Hill Pioneer Settlement"), 
                             (input_files[3], "Ken Done's house")
                             ])
def test_load_pymarc_record(input_file, expected):
    record = load_pymarc_record(input_file)
    title = record.title
    assert title.startswith(expected)

# get_callable_files
def test_get_callable_files():
    files = get_callable_files(data_path)
    expected = [path.join(data_path, "example_01_korean_rare.xml"), 
                path.join(data_path, "example_02_chinese_rare.xml"), 
                path.join(data_path, "example_03_photo_child.xml"), 
                path.join(data_path, "example_04_photo_child.xml")]
    assert files == expected