from os import path
from copy import deepcopy
import pytest
from pymarc import Field, Subfield

from src.xml_load_and_process import *

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


# replace field when string supplied and is whole value
@pytest.mark.parametrize("input_file, source_record, string_field, expected", 
                          [
                             (input_files[0], source_path, "655", "Replaced 655 field. gmgpc"), 
                             (input_files[1], source_path, "037", ""), # case field not in record
                             (input_files[2], source_path, "950", "Replaced 950, only $a left."), 
                             (input_files[3], source_path, "650", "Architecture, Domestic Victoria Fitzroy.")
                             ])    
def test_replace_field_whole_string(input_file, source_record, string_field, expected):
    record = pymarc.parse_xml_to_array(input_file)
    source = pymarc.parse_xml_to_array(source_record)
    result = replace_field(record[0], source[0], string_field)
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
                             (input_files[0], source_path, field_655, "Replaced 655 field. gmgpc"), 
                             (input_files[1], source_path, field_037, ""),
                             (input_files[2], source_path, field_950, "Replaced 950, only $a left."), 
                             (input_files[3], source_path, field_650, "Architecture, Domestic Victoria Fitzroy.")
                             ])    
def test_replace_field_field_object(input_file, source_record, field_object, expected):
    record = pymarc.parse_xml_to_array(input_file)
    source = pymarc.parse_xml_to_array(source_record)
    result = replace_field(record[0], source[0], field_object)
    final = result.get_fields(field_object.tag)[0].value() if len(result.get_fields(field_object.tag)) > 0 else ""
    assert final == expected


def test_fix_655_gmgpc():
    record = pymarc.parse_xml_to_array(photo_example_01)
    fixed_record = fix_655_gmgpc(record[0])
    assert fixed_record.get_fields('655')[0].value() == "Gelatin silver prints. gmgpc"


@pytest.mark.parametrize("input_file, expected", 
                          [
                             (source_path, True), 
                             (input_files[1], False), 
                             (input_files[2], False), 
                             (input_files[3], False)
                             ])
def test_is_parent(input_file, expected):
    record = pymarc.parse_xml_to_array(input_file)
    assert is_parent(record[0]) == expected



def test_subfield_is_in_record_type_handling():
    with pytest.raises(Exception) as e_info:
        subfield_is_in_record("not-a-reord","query","100",'a')

def test_subfield_is_in_record_single_record(single_record):
    record = deepcopy(single_record)
    returned = subfield_is_in_record(record, 'CUASM213/7', '037', 'a')
    assert returned == "CUASM213/7"

def test_subfield_is_in_record_whitespace(single_record):
    record = deepcopy(single_record)
    returned = subfield_is_in_record(record, 'CUASM213 / 7', '037', 'a')
    assert returned == "CUASM213/7"

def test_fix_245_indicators(temp_marc_file):
    with open(temp_marc_file, 'rb') as mf:
        reader = pymarc.MARCReader(mf)
        for record in reader:
            if record['001'].value()=='9939651473607636':
                new_record = fix_245_indicators(record)
                break
    assert new_record['245'].indicator2 == '0'

# 245 fields
field_245_correct_ind2 = [pymarc.Field(
    tag = '245',
    indicators = ['0', '5'],
    subfields = [
        pymarc.Subfield(code='a', value='[The test case] :'),
        pymarc.Subfield(code='b', value='a test /'),
        pymarc.Subfield(code='c', value='Testington Jones')
    ]
)]
# This case is because the program is not capable of fixing human error in recording
# only of replacing empty with data.
field_245_correct_ind2_data_mismatch = [pymarc.Field(
    tag = '245',
    indicators = ['0', '5'],
    subfields = [
        pymarc.Subfield(code='a', value='[Test case] :'), # should be 1
        pymarc.Subfield(code='b', value='a test /'),
        pymarc.Subfield(code='c', value='Testington Jones')
    ]
)]

field_245_incorrect_ind2_bracket = [pymarc.Field(
    tag = '245',
    indicators = ['0', '#'],
    subfields = [
        pymarc.Subfield(code='a', value='[The test case] :'),
        pymarc.Subfield(code='b', value='a test /'),
        pymarc.Subfield(code='c', value='Testington Jones')
    ]
)]

test_245s = [field_245_correct_ind2, field_245_correct_ind2_data_mismatch, field_245_incorrect_ind2_bracket]

@pytest.mark.parametrize("set_field_list", test_245s, indirect=["set_field_list"])
def test_fix_245_only_changes_unset_ind2(field_replace_record):
    record = deepcopy(field_replace_record)
    record = fix_245_indicators(record)
    assert record['245'].indicator2 == '5'

@pytest.mark.parametrize("set_field_list", test_245s, indirect=["set_field_list"])
def test_set_245_ind1_to_1(field_replace_record):
    record = deepcopy(field_replace_record)
    record.remove_fields('100', '110', '111', '130')
    record = fix_245_indicators(record)
    assert record['245'].indicator1 == '1'

@pytest.mark.parametrize("input, expected",
                        [
                            ("The title", 4), 
                            ("[the title",5),
                            ("L'title", 2), 
                            ("xyz", 0), 
                            ('123', 0),
                            ("青春無期徒刑", 0),
                            ("översättning", 0)
                            ]
                            )
def test_get_nonfiling_characters(input, expected):
    assert len(get_nonfiling_characters(input)) == expected

field_830_invalid_ind2_bracket_5 = [pymarc.Field(
    tag = '830',
    indicators = ['0', '#'],
    subfields = [
        pymarc.Subfield(code='a', value='[The test case] :'),
    ]
)]

field_830_invalid_ind2_bracket_0 = [pymarc.Field(
    tag = '830',
    indicators = ['0', '#'],
    subfields = [
        pymarc.Subfield(code='a', value='abcde :'),
    ]
)]

field_830_valid_ind2_bracket = [pymarc.Field(
    tag = '830',
    indicators = ['0', '5'], # wrong value to make sure it doesn't change when set
    subfields = [
        pymarc.Subfield(code='a', value="L'elephant"), # Would be 2 if changed
    ]
)]

test_830s = [field_830_invalid_ind2_bracket_5, field_830_invalid_ind2_bracket_0, field_830_valid_ind2_bracket]

@pytest.mark.parametrize("set_field_list", test_830s, indirect=["set_field_list"])
def test_830_fix_ind2(field_replace_record):
    record = deepcopy(field_replace_record)
    record = fix_830_ind2(record)
    assert record['830'].indicator2 in ['0', '5']

def test_830_fix_when_no_830(single_record):
    record = deepcopy(single_record)
    record.remove_fields('830')
    wr = fix_830_ind2(record)
    assert wr == record
    
bad_773_field = pymarc.Field(
    tag = '773',
    indicators = ['/', '/']
)

def test_fix_773_ind1(single_record):
    record = deepcopy(single_record)
    record.remove_fields('773')
    record.add_ordered_field(bad_773_field)
    wr = fix_773_ind1(record)
    assert wr['773'].indicator1 == "0"

# hard case: ("H2004.65/87a-c",["H2004.65/87a-c","H2004.65/87a-c","H2004.65/87a-c"])
@pytest.mark.parametrize("input, expected", 
                          [
                             ("H83.12/1-5", ["H83.12/1", "H83.12/2", "H83.12/3", "H83.12/4", "H83.12/5"]), 
                             ("RA-1023-12", ["RA-1023-12"]), 
                             ("jkflds", ["jkflds"]),
                             ("MS12345/1/PHO234-235", ["MS12345/1/PHO234","MS12345/1/PHO235"]), 
                             ("RWP/A19.13-15", ["RWP/A19.13","RWP/A19.14","RWP/A19.15"]),
                             ("RWPA19.13-15", ["RWPA19.13-15"]),
                             ("IAN01/01/95/12-13a",["IAN01/01/95/12-13a"])
                          ]
                        )
def test_enumerate_037(input, expected):
    output = enumerate_037(input)
    expected.sort()
    assert output == expected