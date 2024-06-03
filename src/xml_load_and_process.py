import pymarc
import os
import re
import logging
from copy import deepcopy
import re
import dateparser
import dateutil.parser
from datetime import datetime

logger = logging.getLogger()


def fix_655_gmgpc(record):
    """Fixes trailing punctuation from 655 with $2 gmgpc subject headings."""
    fields = record.get_fields("655")

    for field in fields:
        if len(field.get_subfields("2")) > 0:
            field["2"] = (
                "gmgpc" if field["2"].startswith("gmgpc") else field["2"]
            )  # strips out trailing punctuation/whitespace in $2
            value = field["a"] if field["2"] == "gmgpc" else ""

            if (
                not value.endswith(".")
                and "gmgpc" in field["2"]
                and len(field.subfields) == 2  # caveat for gmgpc with $x
            ):  # adds final period to gmgpc if required.
                field["a"] = value + "."

    return record


def is_parent(record):
    """Returns True if 956$b == PARENT"""
    fields = record.get_fields("956")
    for field in fields:
        if field["b"] == "PARENT":
            return True
    return False


# Appears overfitted, could generalise or simplify.
def subfield_is_in_record(record, query, tag, subfield, whitespace=True):
    """Returns matching subfield from a record matching either exact or with whitespace stripped.

    Args:
    record: (pymarc Record object)
    query: (str) - value expected in field
    tag: (str)
    """
    # check record is Record
    if not isinstance(record, pymarc.record.Record):
        raise Exception("Record must be a pymarc Record object.")

    # get the matched accession numbers
    for item in record.get_fields(tag):
        if item[subfield] == query:
            return query
        elif item[subfield].replace(" ", "") == query.replace(" ", ""):
            return item[subfield]
        elif item[subfield].upper() == query.upper():
            return item[subfield]
        # 037 case for ranged identifiers
        elif tag == "037" and "-" in item[subfield]:
            identifiers = enumerate_037(item[subfield])
            for id in identifiers:
                if (
                    id == query
                    or id.replace(" ", "") == query.replace(" ", "")
                    or id.upper() == query.upper()
                ):
                    return id
        else:
            continue

    # log failed records and return None
    for item in record.get_fields(tag):
        try:
            logger.debug(
                f"No match found for {query} in {tag} ${subfield} in record {record['001'].value()}. Record has 037: {item}"
            )
        except Exception as e:
            logger.error(f"Error adding log for failed query search {e}")
    return None


def get_nonfiling_characters(string):
    # \W catches anything that returns False for str.isalnum()
    # Unicode characters in other scripts inherit the Alphabetic property
    # and return True if Alphabetic.
    nonfiling = r"^(\W*the |\W*an |\W*a |\W*le |\W*l')?\s*"
    query = re.search(nonfiling, string.lower())
    return query.group()


def fix_245_indicators(record):
    """Checks aspects of the 245 in a record and updates indicators"""
    wr = deepcopy(record)
    title = wr.title

    # fix first indicator - 0 - No added entry, 1 - Added entry (no 1xx)
    if len(wr.get_fields("100", "110", "111", "130")) == 0:
        first_indicator = "0"
    else:
        first_indicator = "1"
    # If second indicator is not numeric, get nonfiling and calculate length.
    valid_ind2 = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    current_ind2 = wr["245"].indicator2
    if current_ind2 not in valid_ind2:
        prefix_store = get_nonfiling_characters(title)
        if prefix_store is not None:
            second_indicator = str(len(prefix_store))
        else:
            second_indicator = "0"
    else:
        second_indicator = wr["245"].indicator2

    for field in wr.get_fields("245"):
        field.indicator1 = first_indicator
        field.indicator2 = second_indicator
    wr.remove_fields("245")
    wr.add_ordered_field(field)
    return wr


# Fix 773-ind1 : 0 - Display note, 1 - Do not display note
def fix_830_ind2(record):
    # Check if record has 830.
    fix_830 = record.get_fields("830")
    if len(fix_830) == 0:
        return record
    # Process existing 830s
    wr = deepcopy(record)
    wr.remove_fields("830")
    valid_ind2 = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
    for field in fix_830:
        if field.indicator2 not in valid_ind2:
            try:
                title = field["a"]
                field.indicator2 = str(len(get_nonfiling_characters(title.lower())))
                wr.add_ordered_field(field)
            except Exception as e:
                print(f"Error getting subfield $a from 830: {e}")
                logger.error(
                    f"Error for record {wr['001'].value()} getting subfield $a from 830: {e}"
                )
    return record


def fix_773_ind1(record):
    fix_730 = record.get_fields("773")
    if len(fix_730) == 0:
        return record
    wr = deepcopy(record)
    wr.remove_fields("773")
    for field in fix_730:
        if field.indicator1 not in ["0", "1"]:
            field.indicator1 = "0"
        wr.add_ordered_field(field)
    return wr


def fix_1xx_ind2(record):
    xx1 = record.get_fields("100", "110", "111", "130")
    if len(xx1) == 0:
        return record
    wr = deepcopy(record)
    wr.remove_fields("100", "110", "111", "130")
    for field in xx1:
        field.indicator2 = "\\"
        wr.add_ordered_field(field)
    return wr


def fix_indicators(record):
    """Applies fixes for 1xx-ind2, 245-ind1, 245-ind2, 773-ind1, 830-ind2."""
    wr = deepcopy(record)
    wr = fix_1xx_ind2(wr)
    wr = fix_245_indicators(wr)
    wr = fix_773_ind1(wr)
    wr = fix_830_ind2(wr)
    return wr


def make_suffix_list(start, end, text_part=""):
    """
    args:
        start (int) : Numeric start of id range
        end (int) : Numeric end of id range.
        text_part (str) : Identifier prefix, eg PHO. If none, defaults to ""
    """
    output = []
    for item in range(start, end + 1):
        if text_part is not None:
            id = text_part + str(item)
        else:
            id = str(item)
        output.append(id)
    return output


def enumerate_037(id_range):
    """Function for taking id range and returning a list of all identifiers.
    Currently works for identifiers with / character before range and - in range.
    eg. H83.12/1-5, MS12345/1/PHO234-235. If the id cannot be enumerated returns input in a list.
    Does not handle alphabetic suffixes (eg. H2012.12/1a-c)"""
    # if doesn't contain "-" return value as item in list.
    if "-" not in id_range or "/" not in id_range:
        return [id_range]

    # check that range doesn't end with letter
    if not id_range[-1].isnumeric():
        return [id_range]

    # whole part case (eg. "H2012.200/248 - H2012.200/251")
    id_range_stripped = id_range.replace(" ", "")
    part1, part2 = id_range_stripped.split("-")
    if "/" in part1 and "/" in part2:
        root1 = part1[0 : part1.rfind("/")]
        root2 = part2[0 : part2.rfind("/")]
        if root1 == root2:
            id_root = root1
            id_range_stripped = (
                id_root
                + "/"
                + part1[part1.rfind("/") + 1 :]
                + "-"
                + part2[part2.rfind("/") + 1 :]
            )

    # else, split by last index of /
    id_root, id_suffix = (
        id_range_stripped[0 : id_range_stripped.rfind("/")],
        id_range_stripped[id_range_stripped.rfind("/") + 1 :],
    )
    end_part = id_suffix.split("-")

    # declare variables
    text_part_end = None
    text_part_start = None

    if "." in id_suffix:  # RWP has this style
        first_prefix = None
        first_suffix = None
        second_prefix = None
        second_suffix = None
        if "." in end_part[0]:
            first_prefix, first_suffix = end_part[0].split(".")
        else:
            first_suffix = end_part[0]
        if "." in end_part[1]:
            second_prefix, second_suffix = end_part[1].split(".")
        else:
            second_suffix = end_part[1]
        if first_prefix and first_suffix:
            if first_suffix.isnumeric():
                start = int(first_suffix)
                text_part_start = first_prefix
            else:
                return [id_range]
        elif first_suffix:
            if first_suffix.isnumeric():
                start = int(first_suffix)
            else:
                return [id_range]
        if second_prefix and second_suffix:
            if second_suffix.isnumeric():
                end = int(second_suffix)
                text_part_start = second_prefix
            else:
                return [id_range]
        elif second_suffix:
            if second_suffix.isnumeric():
                end = int(second_suffix)
            else:
                return [id_range]

        # check if the text part is the same between both bits
        if text_part_start is not None and text_part_end is not None:
            if text_part_start == text_part_end:
                text_part = text_part_start + "."
            else:
                logger.info(
                    f"Identifier range: {id_range} has conflicting start and end prefixes."
                )
                return [id_range]
        elif text_part_start is not None:
            text_part = text_part_start + "."
        elif text_part_end is not None:
            return [id_range]

        # finalise the . output version.
        suffixes = make_suffix_list(start, end, text_part)
        output = []
        for item in suffixes:
            identifier = id_root + r"/" + item
            output.append(identifier)
        output.sort()
        return output

    # MS and H identifiers
    try:
        first = end_part[0]
    except IndexError:
        return [id_range]
    if not first.isnumeric():
        text_part = re.sub("\d+\.?", "", first)
        num_part = re.sub("\D+", "", first)
        start = int(num_part)
        if text_part is not None:
            if first.startswith(text_part):
                prefix = True
            else:
                suffix = True
    else:
        start = int(first)
        text_part = None

    # Second part
    try:
        second = end_part[1]
    except IndexError:
        return [id_range]
    if not second.isnumeric():
        text_part_second = re.sub("\d+", "", second)
        num_part = re.sub("\D+\.?", "", second)
        start = int(num_part)
        if text_part:
            if not text_part == text_part_second:
                return [id_range]  # something weird if this happens
        else:
            text_part = text_part_second
        if second.startswith(text_part):
            prefix = True
        else:
            suffix = True
        end = int(num_part)
    else:
        end = int(second)

    final_range = make_suffix_list(start, end, text_part)

    # count through output to get final
    output = []
    for item in final_range:
        id = id_root + r"/" + item
        output.append(id)
    output.sort()
    return output


def get_current_008_date(input):
    # Check if string is valid
    if len(input) != 40:
        logger.error("Invalid 008 - length is not 40 characters")
        raise ValueError("Invalid 008 - length is not 40 characters")

    # Check date substring is position 6-14
    substring = r"[a-z]\d\d\d[\du]...."
    current = re.findall(substring, input)
    if len(current) == 0:
        logger.error(
            f"Unable to pattern match date in 008 for input {input} using substring {substring}."
        )
        return None
    elif current[0] != input[6:15]:
        logger.error("Date position 06-14 is not correctly aligned.")
        raise ValueError("Date position 06-14 is not correctly aligned.")
    else:
        return input[6:15]


def parse_008_date(input):
    """Parse 008 from input date string. Converts all inclusive dates to questionable."""
    # Regex for stripping or determining a year value
    circa = "(?<!e)c\.|ca\.|circa|approx\.|approximately"
    year = "\d\d\d\d"

    ## Get dates from String
    years = re.findall(year, input)
    stripped_date = re.sub("\D", "", input)

    ## Try for detailed date
    detailed_date = dateparser.parse(
        re.sub(circa, "", input), languages=["en"], settings={"STRICT_PARSING": True}
    )
    if detailed_date is not None:
        return "e" + detailed_date.strftime("%Y%m%d")

    ## Try for other date types
    if len(stripped_date) == 4 and len(years) == 1:
        if len(re.sub("\W", "", input)) == 4:
            return "s" + stripped_date + "    "
        try:  ## get month.
            detailed_month = dateutil.parser.parse(re.sub("[\[\]\?]", "", input))
            return "e" + detailed_month.strftime("%Y%m  ")
        except Exception as e:
            try:
                detailed_month = datetime.strptime(input, "%b %Y").date()
            except Exception as e:
                return "s" + stripped_date + "    "
    elif len(stripped_date) == 3 and len(re.sub("\D", "", input)) == 3:
        return "s" + stripped_date + "u    "
    elif len(years) == 1 and len(stripped_date) <= 8:
        return "s" + years[0] + "    "
    elif len(stripped_date) == 8 or "between" in input or "or" in input:
        matches = re.findall(year, input)
        return "q" + "".join(matches)
    elif len(years) == 2 and len(stripped_date) > 8:
        return "q" + years[0] + years[1]
    else:
        return None


def replace_many_008_date(record):
    current_008 = record["008"].value()
    try:
        get_current_008_date(current_008)
        current_26xc = record.get_fields("260", "264")
        date_string = None
        for field in current_26xc:
            if field.get("c") is not None:
                if date_string is not None:
                    logger.error(
                        f"Record {record['001'].value()} contains two $c fields in the date area. Requires manual review."
                    )
                    raise ValueError(
                        f"Record {record['001'].value()} contains two $c fields in the date area. Requires manual review."
                    )
                else:
                    date_string = field.get("c")
            else:
                logger.info(f"Record missing 26x $c: {record['001'].value()}")
        if date_string is not None:
            new_008 = parse_008_date(date_string)
            if new_008 == None:
                logger.info(
                    f"Unable to parse date from input string. Probably invalid for record {record['001'].value()} with date string: {date_string} and 008: {record['008'].value()}. 008 will not be replaced."
                )
                return record
            if len(current_008[6:15]) == len(new_008):
                current_008 = str.replace(current_008, current_008[6:15], new_008)
                record.remove_fields("008")
                field_008 = pymarc.Field(tag="008", data=current_008)
                record.add_ordered_field(field_008)
    except ValueError as e:
        logger.error(
            f"Invalid 008 in record {record['001'].value()}. 008 will not be replaced. Error: {e}"
        )
    return record


def replace_tag(tag, field, indicator1=None, indicator2=None):
    """Create a new field with the data from the existing field with the new tag.
    Optionally pass indicators to set those as well.

    Args:
        tag (str) : three digit string indicating the MARC field, eg '100'
        field (pymarc Field object) : Field containing source data.
        indicator1 (str|None) : defaults to None to use existing indicators or submit a single digit string to set.
        indicator2 (str|None) : as indicator1."""
    if indicator1 == None:
        indicator1 = field.indicator1
    if indicator2 == None:
        indicator2 = field.indicator2
    new_field = pymarc.Field(
        tag=tag, indicators=[indicator1, indicator2], subfields=field.subfields
    )
    return new_field


def get_date_from_fields(fields):
    """Creates a 264$c from list of existing 26x"""
    date_data = []
    for field in fields:
        for subfield in field.subfields:
            if parse_008_date(subfield.value) is not None:
                date_data.append(subfield.value)
    logger.info("Dates identified: " + ", ".join(date_data) + ".")
    return date_data


def build_date_field(date_list):
    """Creates a date field from a list of dates. If more than one date, creates a between span."""
    if len(date_list) == 0:
        return None
    elif len(date_list) == 1:
        return date_list[0]
    else:
        list_years = []
        for date in date_list:
            years = re.findall("\d\d\d\d", date)
            list_years.extend(years)
        int_years = []
        for item in list_years:
            if int(item) not in int_years:
                int_years.append(int(item))
        if len(int_years) == 1:
            return str(int_years[0])
        else:
            int_years.sort()
            return "between " + str(int_years[0]) + "? and " + str(int_years[-1]) + "?"


def build_date_production(fields, ind1=" ", ind2="0"):
    """Creates a 264 from fields supplied in a record. Default indicators are #0"""
    dates = get_date_from_fields(fields)
    date = build_date_field(dates)
    if date is None:
        return None
    field = pymarc.Field(
        tag="264",
        indicators=[ind1, ind2],
        subfields=[pymarc.Subfield(code="c", value=date)],
    )
    return field


def check_fields(record, tag_list_a, tag_list_b, subfield=None):
    """Searches for sets of tags on a record and checks if list a matches list b. Option to limit to a subfield."""
    list_a = record.get_fields(*tag_list_a)
    list_b = record.get_fields(*tag_list_b)
    target_fields = [str(x) for x in list_b]
    positive = False
    for field in list_a:
        if subfield == None:
            match_data = str(field)[8:]
        else:
            match_data = field.get(subfield)
        if match_data == None:
            return False
        for item in target_fields:
            if match_data in item:
                logger.warning(
                    f"Warning: Record {record['001'].value()} has matching data for field {str(field)} and matching 7xx {item}"
                )
                print(
                    f"Warning: Record {record['001'].value()} has matching data for field {str(field)} and matching 7xx {item}"
                )
                positive = True

    return positive
