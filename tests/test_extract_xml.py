from os import path
import pytest

from src.extract_xml import *

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

@pytest.mark.parametrize("input, expected", [(single_file_read, 1), (spec_char_input_read, 3)])
def test_get_records_from_json_dictionary_size(input, expected):
    records = get_record_from_json(input)
    assert len(records) == expected


@pytest.mark.parametrize("input, expected, id", [(single_file_read, single_file_expected_read, single_file_id), (spec_char_input_read, spec_char_xml_read, spec_char_id)])
def test_get_record_from_json_first_matches_expected(input, expected, id):
    test_data = input
    expected_data = expected
    records = get_record_from_json(test_data)
    target = records[id][0]
    assert target == expected_data

xml_header_pass = "<?xml version=\"1.0\" encoding=\"UTF-16\"?><record>record content</record>"
xml_no_header_pass = r"<record>record content</record>"

@pytest.mark.parametrize("input, expected", [(xml_header_pass, "<record>"), (xml_no_header_pass, "<record>")])
def test_fix_xml_header_encoding(input, expected):
    header_replaced = fix_xml_header_encoding(input)
    assert header_replaced.startswith(expected)
    assert header_replaced.endswith(expected.replace("<", "</"))

@pytest.mark.parametrize("input", [("xyz"), ("1234")])
def test_fix_xml_header_error_handling(input):
    header_replaced = fix_xml_header_encoding(input)
    assert header_replaced == None