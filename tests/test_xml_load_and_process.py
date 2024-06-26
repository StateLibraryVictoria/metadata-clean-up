from os import path
from copy import deepcopy
import pytest
from pymarc import Field, Subfield, Record

from src.xml_load_and_process import *


# Setup test data
def load_test_files(filename):
    data = open(
        os.path.join(filename), "r", encoding="utf-8", errors="backslashreplace"
    )
    return data.read()


ROOT_DIR = os.path.abspath(os.curdir)


## Type should be input or expected
def create_file_array(test_data, type):
    input_path = os.path.join(test_data, type)
    for root, dir, files in os.walk(input_path):
        files.sort()
        output_list = [path.join(input_path, file) for file in files]
    return output_list


data_path = path.join(ROOT_DIR, "tests", "test_data", "xml_load_and_process")
input_path = os.path.join(data_path, "input")

## input files
input_files = create_file_array(data_path, "input")
korean_example = input_files[0]
chinese_example = input_files[1]
photo_example_01 = input_files[2]
photo_example_02 = input_files[3]

source_path = os.path.join(data_path, "source", "source_record.xml")
source_record = load_test_files(source_path)


field_655 = Field(
    tag="655",
    indicators=["", "7"],
    subfields=[Subfield(code="a", value="value"), Subfield(code="2", value="value")],
)

field_037 = Field(
    tag="037", indicators=["", ""], subfields=[Subfield(code="a", value="value")]
)
field_950 = Field(
    tag="950", indicators=["", ""], subfields=[Subfield(code="a", value="value")]
)

field_650 = Field(
    tag="650", indicators=["", ""], subfields=[Subfield(code="a", value="value")]
)


def test_fix_655_gmgpc():
    record = pymarc.parse_xml_to_array(photo_example_01)
    fixed_record = fix_655_gmgpc(record[0])
    assert fixed_record.get_fields("655")[0].value() == "Gelatin silver prints. gmgpc"


def test_fix_655_gmgpc_x():
    record = pymarc.Record()
    record.add_field(
        pymarc.Field(
            tag="655",
            indicators=[" ", "7"],
            subfields=[
                pymarc.Subfield("a", "Slides"),
                pymarc.Subfield("x", "Color."),
                pymarc.Subfield("2", "gmgpc"),
            ],
        )
    )
    print(str(record))
    fixed_record = fix_655_gmgpc(record)
    assert str(fixed_record["655"]) == "=655  \\7$aSlides$xColor.$2gmgpc"


def test_fix_655_aat():
    record = pymarc.Record()
    record.add_field(
        pymarc.Field(
            tag="655",
            indicators=[" ", "7"],
            subfields=[
                pymarc.Subfield("a", "photographs"),
                pymarc.Subfield("2", "aat"),
            ],
        )
    )
    print(str(record))
    fixed_record = fix_655_gmgpc(record)
    assert str(fixed_record["655"]) == "=655  \\7$aphotographs$2aat"


@pytest.mark.parametrize(
    "input_file, expected",
    [
        (source_path, True),
        (input_files[1], False),
        (input_files[2], False),
        (input_files[3], False),
    ],
)
def test_is_parent(input_file, expected):
    record = pymarc.parse_xml_to_array(input_file)
    assert is_parent(record[0]) == expected


def test_subfield_is_in_record_type_handling():
    with pytest.raises(Exception) as e_info:
        subfield_is_in_record("not-a-reord", "query", "100", "a")


def test_subfield_is_in_record_single_record(single_record):
    record = deepcopy(single_record)
    returned = subfield_is_in_record(record, "CUASM213/7", "037", "a")
    assert returned == "CUASM213/7"


def test_subfield_is_in_record_whitespace(single_record):
    record = deepcopy(single_record)
    returned = subfield_is_in_record(record, "CUASM213 / 7", "037", "a")
    assert returned == "CUASM213/7"


# test range case.
test_037_range = Record()
h_field = Field(
    tag="037", indicators=["", ""], subfields=[Subfield(code="a", value="H2013.12/1-5")]
)

rwp_field = Field(
    tag="037",
    indicators=["", ""],
    subfields=[Subfield(code="a", value="rwp/A19.13-15")],
)

ms_field = Field(
    tag="037",
    indicators=["", ""],
    subfields=[Subfield(code="a", value="MS12345/1/PHO234-235")],
)


def test_subfield_is_in_record_range_hnum():
    record = deepcopy(test_037_range)
    record.add_field(h_field)
    returned = subfield_is_in_record(record, "H2013.12/2", "037", "a")
    assert returned == "H2013.12/2"


def test_subfield_is_in_record_range_end_num(single_record):
    record = single_record
    record.add_ordered_field(ms_field)
    for field in record.get_fields("037"):
        print(field)
    returned = subfield_is_in_record(record, "MS12345/1/PHO235", "037", "a")
    assert returned == "MS12345/1/PHO235"


def test_subfield_is_in_record_range_period():
    record = deepcopy(test_037_range)
    record.add_field(rwp_field)
    returned = subfield_is_in_record(record, "RWP/A19.14", "037", "a")
    assert returned == "rwp/A19.14"


def test_fix_245_indicators(temp_marc_file):
    with open(temp_marc_file, "rb") as mf:
        reader = pymarc.MARCReader(mf)
        for record in reader:
            if record["001"].value() == "9939651473607636":
                new_record = fix_245_indicators(record)
                break
    assert new_record["245"].indicator2 == "0"


# 245 fields
field_245_correct_ind2 = [
    pymarc.Field(
        tag="245",
        indicators=["0", "5"],
        subfields=[
            pymarc.Subfield(code="a", value="[The test case] :"),
            pymarc.Subfield(code="b", value="a test /"),
            pymarc.Subfield(code="c", value="Testington Jones"),
        ],
    )
]
# This case is because the program is not capable of fixing human error in recording
# only of replacing empty with data.
field_245_correct_ind2_data_mismatch = [
    pymarc.Field(
        tag="245",
        indicators=["0", "5"],
        subfields=[
            pymarc.Subfield(code="a", value="[Test case] :"),  # should be 1
            pymarc.Subfield(code="b", value="a test /"),
            pymarc.Subfield(code="c", value="Testington Jones"),
        ],
    )
]

field_245_incorrect_ind2_bracket = [
    pymarc.Field(
        tag="245",
        indicators=["0", "#"],
        subfields=[
            pymarc.Subfield(code="a", value="[The test case] :"),
            pymarc.Subfield(code="b", value="a test /"),
            pymarc.Subfield(code="c", value="Testington Jones"),
        ],
    )
]

test_245s = [
    field_245_correct_ind2,
    field_245_correct_ind2_data_mismatch,
    field_245_incorrect_ind2_bracket,
]


@pytest.mark.parametrize("set_field_list", test_245s, indirect=["set_field_list"])
def test_fix_245_only_changes_unset_ind2(field_replace_record):
    record = deepcopy(field_replace_record)
    record = fix_245_indicators(record)
    assert record["245"].indicator2 == "5"


@pytest.mark.parametrize("set_field_list", test_245s, indirect=["set_field_list"])
def test_set_245_ind1_to_1(field_replace_record):
    record = deepcopy(field_replace_record)
    record.remove_fields("100", "110", "111", "130")
    record = fix_245_indicators(record)
    assert record["245"].indicator1 == "0"


@pytest.mark.parametrize(
    "input, expected",
    [
        ("The title", 4),
        ("[the title", 5),
        ("L'title", 2),
        ('"title"', 0),
        ("[title]", 0),
        ("xyz", 0),
        ("123", 0),
        ("青春無期徒刑", 0),
        ("översättning", 0),
    ],
)
def test_get_nonfiling_characters(input, expected):
    assert len(get_nonfiling_characters(input)) == expected


field_830_invalid_ind2_bracket_5 = [
    pymarc.Field(
        tag="830",
        indicators=["0", "#"],
        subfields=[
            pymarc.Subfield(code="a", value="[The test case] :"),
        ],
    )
]

field_830_invalid_ind2_bracket_0 = [
    pymarc.Field(
        tag="830",
        indicators=["0", "#"],
        subfields=[
            pymarc.Subfield(code="a", value="abcde :"),
        ],
    )
]

field_830_valid_ind2_bracket = [
    pymarc.Field(
        tag="830",
        indicators=["0", "5"],  # wrong value to make sure it doesn't change when set
        subfields=[
            pymarc.Subfield(code="a", value="L'elephant"),  # Would be 2 if changed
        ],
    )
]

test_830s = [
    field_830_invalid_ind2_bracket_5,
    field_830_invalid_ind2_bracket_0,
    field_830_valid_ind2_bracket,
]


@pytest.mark.parametrize("set_field_list", test_830s, indirect=["set_field_list"])
def test_830_fix_ind2(field_replace_record):
    record = deepcopy(field_replace_record)
    record = fix_830_ind2(record)
    assert record["830"].indicator2 in ["0", "5"]


def test_830_fix_when_no_830(single_record):
    record = deepcopy(single_record)
    record.remove_fields("830")
    wr = fix_830_ind2(record)
    assert wr == record


bad_773_field = pymarc.Field(tag="773", indicators=["/", "/"])


def test_fix_773_ind1(single_record):
    record = deepcopy(single_record)
    record.remove_fields("773")
    record.add_ordered_field(bad_773_field)
    wr = fix_773_ind1(record)
    assert wr["773"].indicator1 == "0"


# Edge cases not yet integrated "H16964-H16981", "MS 1433-MS 1447"
@pytest.mark.parametrize(
    "input, expected",
    [
        ("H83.12/1-5", ["H83.12/1", "H83.12/2", "H83.12/3", "H83.12/4", "H83.12/5"]),
        ("RA-1023-12", ["RA-1023-12"]),
        ("jkflds", ["jkflds"]),
        ("MS12345/1/PHO234-235", ["MS12345/1/PHO234", "MS12345/1/PHO235"]),
        ("RWP/A19.13-15", ["RWP/A19.13", "RWP/A19.14", "RWP/A19.15"]),
        ("RWPA19.13-15", ["RWPA19.13-15"]),
        ("IAN01/01/95/12-13a", ["IAN01/01/95/12-13a"]),
        (
            "H2012.200/248 - H2012.200/251",
            ["H2012.200/248", "H2012.200/249", "H2012.200/250", "H2012.200/251"],
        ),
        ("H2012.12/12 - H2013.13/13", ["H2012.12/12 - H2013.13/13"]),
    ],
)
def test_enumerate_037(input, expected):
    output = enumerate_037(input)
    expected.sort()
    assert output == expected


@pytest.mark.parametrize(
    "input, expected",
    [
        ("240221s1975    vrannn        o   kneng d", "s1975    "),
        ("150216m19061910xx c   gr         0d    c", "m19061910"),
        ("221125i1906####xx#nnn########o###knzxx#d", "i1906####"),
        ("221125s1954    xx#nnn########o###knzxx#d", "s1954    "),
        ("221125scirca 197    n########o###knzxx#d", None),
        ("221125i1921####xx#nnn########o###knzxx#d", "i1921####"),
        ("221125i1920####xx#nnn########o###knzxx#d", "i1920####"),
    ],
)
def test_get_current_008_date(input, expected):
    date = get_current_008_date(input)
    assert date == expected


def test_get_current_008_date_raises_wrong_length():
    with pytest.raises(ValueError):
        get_current_008_date("020419i19211923xx nnn g knzxx d")


def test_get_current_008_date_raises_wrong_alignment():
    with pytest.raises(ValueError):
        get_current_008_date("240221vrannns1975            o   kneng d")


@pytest.mark.parametrize(
    "input, expected",
    [
        ("1970", "s1970    "),
        ("[ca. 1970]", "s1970    "),
        ("January - June 1970", "s1970    "),
        ("[197-?]", "s197u    "),
        ("[between 1970 and 1974?] ", "q19701974"),
        ("ca. 1970-1974", "q19701974"),
        ("c. 1970-c. 1974", "q19701974"),
        ("1970 or 1974", "q19701974"),
        ("1 Jan. 1970-2 Feb. 1974 ", "q19701974"),
        ("February 23, 1970", "e19700223"),
        ("[Jan. 1, 1970]", "e19700101"),
        ("10 January 1974 ", "e19740110"),
        ("Jan. 1970", "e197001  "),
        ("[ca. 1920 - ca. 1954].", "q19201954"),
        ("[Dec. 19, 1972]", "e19721219"),
        ("[May 7-8, 1982]", "s1982    "),
        ("Jan. 18-Feb. 10, 1952", "s1952    "),
    ],
)
def test_parse_008_date(input, expected):
    output = parse_008_date(input)
    assert output == expected


def test_replace_many_008_date(single_record):
    wr = deepcopy(single_record)
    print(wr.get_fields("260", "264"))
    print(wr["008"].value())
    nr = replace_many_008_date(wr)
    new_008 = nr["008"].value()
    assert new_008 == "160406q19701974xx nnn g          knzxx d"


@pytest.mark.parametrize(
    "input, expected",
    [
        (
            pymarc.Field(
                "260",
                indicators=["\\", "0"],
                subfields=[pymarc.Subfield(code="c", value="[between 1920 and 1940?]")],
            ),
            "=264  \\0$c[between 1920 and 1940?]",
        ),
        (
            pymarc.Field(
                "245",
                indicators=[" ", " "],
                subfields=[
                    pymarc.Subfield(code="a", value="Title :"),
                    pymarc.Subfield(code="b", value="a short story."),
                ],
            ),
            "=264  \\\\$aTitle :$ba short story.",
        ),
    ],
)
def test_replace_tag(input, expected):
    test_field = replace_tag("264", input)
    print(test_field.indicators)
    assert str(test_field) == expected


def test_get_date_from_fields():
    field = Field(
        tag="260", indicators=[" ", " "], subfields=[Subfield("c", "[1956?]")]
    )
    no_date_field = Field(
        tag="260", indicators=[" ", " "], subfields=[Subfield("c", "not a date")]
    )
    g_date = Field(
        tag="100",
        indicators=["1", "2"],
        subfields=[
            Subfield("a", "London : "),
            Subfield("b", "Simpkin , Marshal, Hamilton, Kent & Co. ; "),
            Subfield("g", "[ca. 1880 - ca. 1884]"),
        ],
    )
    new_field = get_date_from_fields([field, no_date_field, g_date])
    assert new_field == ["[1956?]", "[ca. 1880 - ca. 1884]"]


@pytest.mark.parametrize(
    "input, expected",
    [
        (["1970"], "1970"),
        (["[ca. 1970]"], "[ca. 1970]"),
        (["January - June 1970", "1970"], "1970"),
        (["[197-?]"], "[197-?]"),
        (["[between 1969 and 1970?]", "10 January 1974 "], "between 1969? and 1974?"),
        (
            ["[between 1969 and 1970?]", "10 January 1974 ", "Jan. 1952"],
            "between 1952? and 1974?",
        ),
    ],
)
def test_build_date_field(input, expected):
    output = build_date_field(input)
    assert output == expected


def test_build_date_production():
    field = Field(tag="260", indicators=[" ", " "], subfields=[Subfield("c", "[1956]")])
    no_date_field = Field(
        tag="260", indicators=[" ", " "], subfields=[Subfield("c", "not a date")]
    )
    g_date = Field(
        tag="100",
        indicators=["1", "2"],
        subfields=[
            Subfield("a", "London : "),
            Subfield("b", "Simpkin , Marshal, Hamilton, Kent & Co. ; "),
            Subfield("g", "[ca. 1880 - ca. 1884]"),
        ],
    )
    date_production = build_date_production([field, no_date_field, g_date])
    assert str(date_production) == "=264  \\0$cbetween 1880? and 1956?"


@pytest.mark.parametrize(
    "input_a, input_b, input_c, expected",
    [
        (("100", "110", "111", "130"), ("700", "710", "711", "720", "730"), "a", True),
        (("100", "110", "111", "130"), ("260", "264"), "a", False),
        (("100", "110", "111", "130"), ("700", "710", "711", "720", "730"), None, True),
        (("100", "110", "111", "130"), ("700", "710", "711", "720", "730"), "b", False),
    ],
)
def test_check_fields(single_record, input_a, input_b, input_c, expected):
    single_record.add_ordered_field(
        pymarc.Field(
            "710",
            indicators=[" ", " "],
            subfields=[
                Subfield(
                    code="a", value="Committee for Urban Action (Melbourne, Vic.)"
                ),
                Subfield(code="b", value="Something"),
            ],
        )
    )
    outcome = check_fields(
        single_record,
        input_a,
        input_b,
        input_c,
    )
    assert outcome == expected
