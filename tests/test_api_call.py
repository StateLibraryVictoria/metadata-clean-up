import os
import pytest

from src.api_call import *

# Read the file into the program.
# Write second version of test_split.


# Checks that lists of mms_ids are split correctly. Includes invalid MMS Ids that should be removed.
@pytest.mark.parametrize(
    "mms_ids, split, count",
    [
        ("9938164143607636", ["9938164143607636"], 1),
        (
            "9938036653607636,9938036613607636,9938164143607636",
            ["9938036653607636", "9938036613607636", "9938164143607636"],
            3,
        ),
        ("9938036653607636,997636,not an mms id", ["9938036653607636"], 1),
    ],
)
def test_split_identifiers(mms_ids, split, count):
    list_ids = split_identifiers(mms_ids)
    assert list_ids == split
    assert len(list_ids) == count


# This would be better if it could check an example with more than 100 ids. Currently just checks a few to make sure the formatting comes out right.
@pytest.mark.parametrize(
    "mms_ids, chunked",
    [
        (["9938164143607636"], {"0": "9938164143607636"}),
        (
            ["9938036653607636", "9938036613607636", "9938164143607636"],
            {"0": "9938036653607636,9938036613607636,9938164143607636"},
        ),
    ],
)
def test_chunk_identifiers(mms_ids, chunked):
    chunked_identifiers = chunk_identifiers(mms_ids)
    assert chunked_identifiers == chunked


# Checks if the MMS Id validator is behaving as expected. Can only test for obvious issues such as not long enough and not starting and ending with the right characters.""
@pytest.mark.parametrize(
    "id, expected",
    [
        ("9938164143607636", True),
        ("997636", False),
        ("not an mms id", False),
        ("99also_not", False),
        ("999912376367636", False),
        ("999912347636", True),
    ],
)
def test_validate_mmsid(id, expected):
    assert validate_mmsid(id) == expected


# Checks that the API key is configured correctly. This does call the API.
def test_check_api_key():
    assert check_api_key() == True
