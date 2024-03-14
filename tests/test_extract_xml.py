from os import path
import pytest

from extract_xml import *

## Define paths
extract_xml_test_path = path.join("tests","test_data","extract_xml")
input_path = path.join(extract_xml_test_path, "input")
expected_path = path.join(extract_xml_test_path, "expected")

## Single item example
single_record = "example_1_record.json"
single_path = path.join(input_path, single_record)
single_file_open = open(single_path, 'r', encoding="ascii", errors='backslashreplace')
single_file_read = single_file_open.read()
single_file_id = "9939772237507636"
single_file_expected = open(path.join(expected_path, f"record_{single_file_id}.xml"), 'r', encoding="utf-8", errors='backslashreplace')
single_file_expected_read = single_file_expected.read()

## Special character example
example_json_special_char = "json_language_encoding.json"
spec_char_file_path = path.join(input_path, example_json_special_char)
spec_char_input_file = open(spec_char_file_path, 'r', encoding="ascii", errors='backslashreplace')
spec_char_id = "9938036653607636"
spec_char_expected_xml = open(path.join(expected_path, f"record_{spec_char_id}.xml"), 'r', encoding="utf-8", errors='backslashreplace')
spec_char_input_read = spec_char_input_file.read()
spec_char_xml_read = spec_char_expected_xml.read()

## Tests

@pytest.mark.parametrize("input, local_path", [(single_file_read, single_path), (spec_char_input_read, spec_char_file_path)])
def test_open_files(input, local_path):
    file = open_files(local_path)
    comparison = input
    assert len(file) > 0
    assert file == comparison

@pytest.mark.parametrize("input, expected", [(single_file_read, 1), (spec_char_input_read, 3)])
def test_get_records_dictionary_size(input, expected):
    records = get_record(input)
    assert len(records) == expected


@pytest.mark.parametrize("input, expected, id", [(single_file_read, single_file_expected_read, single_file_id), (spec_char_input_read, spec_char_xml_read, spec_char_id)])
def test_get_records_first_matches_expected(input, expected, id):
    test_data = input
    expected_data = expected
    records = get_record(test_data)
    target = records[id][0]
    print(target)
    assert target == expected_data

@pytest.mark.parametrize("input, expected, id", [(single_file_read, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>", single_file_id), (spec_char_input_read, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>", spec_char_id)])
def test_fix_header_encoding(input, expected, id):
    test_data = input
    records = get_record(test_data)
    header_replaced = fix_header_encoding(records)
    target = header_replaced[id][0]
    assert target.startswith(expected)


