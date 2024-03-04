import requests
from os import path
from datetime import datetime
import pytest

from api_call import *

@pytest.mark.parametrize("mms_ids, split, count", 
                         [("9938164143607636", ["9938164143607636"], 1), ("9938036653607636,9938036613607636,9938164143607636", ["9938036653607636","9938036613607636","9938164143607636"], 3), ("9938036653607636,997636,not an mms id", ["9938036653607636"], 1)])
def test_split_identifiers(mms_ids, split, count):
    list_ids = split_identifiers(mms_ids)
    assert list_ids == split
    assert len(list_ids) == count

# Checks that valid MMS ids are returned and invalid ones are not.
@pytest.mark.parametrize("mms_ids, chunked", [(["9938164143607636"], {'0': "9938164143607636"} ), (["9938036653607636","9938036613607636","9938164143607636"], {'0': "9938036653607636,9938036613607636,9938164143607636"})])
def test_chunk_identifiers(mms_ids, chunked):
    chunked_identifiers = chunk_identifiers(mms_ids)
    assert chunked_identifiers == chunked

@pytest.mark.parametrize("id, expected", [("9938164143607636", True), ("997636", False), ("not an mms id", False), ("99alsonot", False)])
def test_validate_mmsid(id, expected):
    assert validate_mmsid(id) == expected

#@pytest.mark.parametrize("id, expected", [("fds", False), ("997636", False)])
#def test_empty_chunks_bibs(id, expected):
#    assert get_bibs(id) == expected

def test_check_api_key():
    assert check_api_key() == True

def test_output_bib_files(tmp_path):
    location = tmp_path / "json"
    location.mkdir()
    part = '0'
    input = "some text"
    today = datetime.now().strftime('%d%m%Y%H%M00')
    output_bib_files(location, part, input)
    filename = f"{today}_records_batch_{part}.json"
    file = location / filename
    assert file.read_text() == "some text"
    assert len(list(tmp_path.iterdir())) == 1

#def test_get_json_string():
