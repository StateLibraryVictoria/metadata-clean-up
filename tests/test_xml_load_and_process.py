from os import path
import pytest
from pymarc import Field, Subfield

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
input_path = os.path.join(data_path,'input')

## input files
input_files = create_file_array(data_path, "input")
korean_example = input_files[0]
chinese_example = input_files[1]
photo_example_01 = input_files[2]
photo_example_02 = input_files[3]

source_path = os.path.join(data_path, "source", "source_record.xml")
source_record = load_test_files(source_path)

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
    files = get_callable_files(input_path)
    expected = [path.join(input_path, "example_01_korean_rare.xml"), 
                path.join(input_path, "example_02_chinese_rare.xml"), 
                path.join(input_path, "example_03_photo_child.xml"), 
                path.join(input_path, "example_04_photo_child.xml")]
    assert files == expected

# get field count
@pytest.mark.parametrize("input_file, expected", 
                          [
                             (input_files[0], 2), 
                             (input_files[1], 1), 
                             (input_files[2], 1), 
                             (input_files[3], 2)
                             ])
def test_get_field_count(input_file, expected):
    record = load_pymarc_record(input_file)
    field_count = get_field_count(record, "655")
    assert field_count == expected


# replace field when string supplied and is whole value
@pytest.mark.parametrize("input_file, source_record, string_field, expected", 
                          [
                             (input_files[0], source_path, "655", "Replaced 655 field gmgpc"), 
                             (input_files[1], source_path, "037", ""), # case field not in record
                             (input_files[2], source_path, "950", "Replaced 950, only $a left."), 
                             (input_files[3], source_path, "650", "Celebrities Australia Pictorial works.") # case too many fields
                             ])    
def test_replace_field_whole_string(input_file, source_record, string_field, expected):
    record = load_pymarc_record(input_file)
    source = load_pymarc_record(source_record)
    result = replace_field(record, source, string_field)
    final = result.get_fields(string_field)[0].value() if len(result.get_fields(string_field)) > 0 else ""
    assert final == expected

field_655 = Field(
    tag = '655',
    indicators = ['', '7'],
    subfields = [
        Subfield(code='a', value='value'),
        Subfield(code='2', value='value')
    ])

field_037 = Field(
    tag = '037',
    indicators = ['', ''],
    subfields = [
        Subfield(code='a', value='value')
    ]
)
field_950 = Field(
    tag = '950',
    indicators = ['', ''],
    subfields = [
        Subfield(code='a', value='value')
    ]
)

field_650 = Field(
    tag = '650',
    indicators = ['', ''],
    subfields = [
        Subfield(code='a', value='value')
    ]
)

# replace field when field supplied and is whole value
@pytest.mark.parametrize("input_file, source_record, field_object, expected", 
                          [
                             (input_files[0], source_path, field_655, "Replaced 655 field gmgpc"), 
                             (input_files[1], source_path, field_037, ""),
                             (input_files[2], source_path, field_950, "Replaced 950, only $a left."), 
                             (input_files[3], source_path, field_650, "Celebrities Australia Pictorial works.")
                             ])    
def test_replace_field_field_object(input_file, source_record, field_object, expected):
    record = load_pymarc_record(input_file)
    source = load_pymarc_record(source_record)
    result = replace_field(record, source, field_object)
    final = result.get_fields(field_object.tag)[0].value() if len(result.get_fields(field_object.tag)) > 0 else ""
    assert final == expected


def test_fix_655_gmgpc():
    record = load_pymarc_record(photo_example_01)
    fixed_record = fix_655_gmgpc(record)
    assert fixed_record.get_fields('655')[0].value() == "Gelatin silver prints gmgpc"