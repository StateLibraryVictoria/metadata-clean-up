import pytest
from src.get_parent_ids import *
from src.xml_load_and_process import get_callable_files, load_pymarc_record

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
    record = load_pymarc_record(input_file)
    id = get_parent_id(record)
    assert id == expected


def test_iterate_get_parent():
    id_list = iterate_get_parents(input_files)
    assert id_list == {"9939647808307636":"9916783623607636", "9939647812307636": "9922700093607636"}