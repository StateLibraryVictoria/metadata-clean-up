from os import path
import pytest

from extract_xml import *

## Define paths
extract_xml_test_path = path.join("tests","test_data","extract_xml")
input_path = path.join(extract_xml_test_path, "input")
expected_path = path.join(extract_xml_test_path, "expected")

## Simple example (100 records)
simple_100_records = "simple_100_records.json"
simple_100_path = path.join(input_path, simple_100_records)
simple_100_open = open(simple_100_path, 'r', encoding="ascii", errors='backslashreplace')
simple_100_id = "9939647582007636"
simple_100_first_expected = open(path.join(expected_path, f"record_{simple_100_id}.xml"), 'r', encoding="utf-8", errors='backslashreplace')


## Special character example
example_json_special_char = "json_language_encoding.json"
spec_char_file_path = path.join(input_path, example_json_special_char)
spec_char_input_file = open(spec_char_file_path, 'r', encoding="ascii", errors='backslashreplace')
spec_char_id = "9938036653607636"
spec_char_expected_xml = open(path.join(expected_path, f"record_{spec_char_id}.xml"), 'r', encoding="utf-8", errors='backslashreplace')


## Tests

@pytest.mark.parametrize("input, local_path", [(simple_100_open, simple_100_path), (spec_char_input_file, spec_char_file_path)])
def test_open_files(input, local_path):
    file = open_files(local_path)
    comparison = input.read()
    assert len(file) > 0
    assert file == comparison

@pytest.mark.parametrize("input, expected", [(simple_100_open, 100), (spec_char_input_file, 3)])
def test_get_records_dictionary_size(input, expected):
    records = get_record(input.read())
    assert len(records) == expected


@pytest.mark.parametrize("input, expected, id", [(simple_100_open, simple_100_first_expected, simple_100_id), (spec_char_input_file, spec_char_expected_xml, spec_char_id)])
def test_get_records_first_matches_expected(input, expected, id):
    test_data = input.read()
    expected_data = expected.read()
    records = get_record(test_data)
    target = records[id][0]
    assert target == expected_data

@pytest.mark.parametrize("input, expected, id", [(simple_100_open, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>", simple_100_id), (spec_char_input_file, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>", spec_char_id)])
def test_fix_header_encoding(input, expected, id):
    test_data = input.read()
    records = get_record(test_data)
    header_replaced = fix_header_encoding(records)
    target = header_replaced[id][0]
    assert target.startswith(expected)


