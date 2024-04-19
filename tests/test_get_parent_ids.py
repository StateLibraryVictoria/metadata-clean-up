import pytest
import pymarc
from src.get_parent_ids import *
from src.shared_functions import get_callable_files

id_list = "9938036653607636,9938036613607636,9938164143607636".split(",")

data_path = path.join("tests","test_data","xml_load_and_process","input")

input_files = get_callable_files(data_path)
korean_example = input_files[0]
chinese_example = input_files[1]
photo_example_01 = input_files[2]
photo_example_02 = input_files[3]


def test_format_ids_for_api():
    formatted = format_ids_for_api(id_list)
    assert formatted == "9938036653607636,9938036613607636,9938164143607636"


@pytest.mark.parametrize("input_file, expected", 
                         [
                             (input_files[0], None), 
                             (input_files[1], None), 
                             (input_files[2], "9916783623607636"), 
                             (input_files[3], "9922700093607636")
                             ])
def test_get_parent_id(input_file, expected):
    record = pymarc.parse_xml_to_array(input_file)
    id = get_parent_id(record[0])
    assert id == expected


def test_iterate_get_parent():
    id_list = iterate_get_parents(input_files)
    assert id_list[0] == ["9939647808307636", "9916783623607636"]
    assert id_list[1] == ["9939647812307636", "9922700093607636"]
    
good_246 = pymarc.Field(
    tag = '246',
    indicators = ['0', '5'], # arbitrary values
    subfields = [
        pymarc.Subfield(code='a', value="The result we want"), 
        pymarc.Subfield(code='i', value="Some kind of note")
    ]
)

bad_246 = pymarc.Field(
    tag = '246',
    indicators = [' ', ' '], # wrong value to make sure it doesn't change when set
    subfields = [
        pymarc.Subfield(code='a', value="The result we have"), # Would be 2 if changed
    ]
)

fine_246 = pymarc.Field(
    tag = '246',
    indicators = [' ', '1'], # wrong value to make sure it doesn't change when set
    subfields = [
        pymarc.Subfield(code='a', value="The result we have"), # Would be 2 if changed
    ]
)


# big bang cleanup unit tests.
def test_big_bang_cleanup_246_replaces(single_record):
    parent = deepcopy(single_record)
    parent.add_field(good_246)
    many = deepcopy(single_record)
    many.add_field(bad_246)
    many = big_bang_replace(many, parent)
    assert many['246']['a'] == "The result we want"
    assert many['246']['i'] == "Some kind of note"

def test_big_bang_cleanup_246_indicator(single_record):
    parent = deepcopy(single_record)
    parent.add_field(good_246)
    many = deepcopy(single_record)
    many.add_field(fine_246)
    many = big_bang_replace(many, parent)
    assert many['246']['a'] == "The result we have"