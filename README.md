# Metadata Clean-up Project

A Code Club project to create some tools to help clean-up metadata in the Library's catalogue systems.

# Getting started

## Parent records and Many records

To support access to digitised material, MARC records have been generated for digital objects based on their original catalogue records. The original records are referred to as `parent records` while their linked derivatives are referred to as `many records`. These records have specialised local fields in the `950` and `956` which support metadata flows. This process has been developed to simplify cleanup of the `many records`, so many of the methods are designed to work with the relationships between the metadata in these records.

## Installation and setup

Note that for the instructions below, the command `python -m` may be required at the start of each command to add modules to path.

- [Install Pipenv](https://pipenv.pypa.io/en/latest/installation.html#installing-pipenv) using the command `$ pip install pipenv --user`.
- Install dependencies using `pipenv install` to install requirements in `Pipfile`. Requirements are also stored in `requirements.txt`.
- Create a local `.env` file based of the file `env.example` to add required API key and other secret variables.
- When writing scripts use `setup_directories()` function in `shared_functions.py` to make required directories before running.
- Run `pipenv shell` to start the environment.
- Run scripts in shell. Check the log file in `logs/` for any output errors.
- Optional: Install [MarcEdit](https://marcedit.reeset.net/) (See Non-python dependencies below)


## Dependencies

Use this space to track additional libraries relied on in the code.

### Whole project
- [json](https://docs.python.org/3/library/json.html)
- [logging](https://docs.python.org/3/library/logging.html)
- [openpyxl](https://openpyxl.readthedocs.io/en/stable/)
- [os](https://docs.python.org/3/library/os.html)
- [pandas](https://pandas.pydata.org/)
- [pipenv](https://pipenv.pypa.io/en/latest/)
- [pymarc](https://pymarc.readthedocs.io/en/latest/)
- [pytest](https://docs.pytest.org/en/8.0.x/)
- [requests](https://requests.readthedocs.io/en/latest/)
- [subprocess](https://docs.python.org/3/library/subprocess.html)
- [sys](https://docs.python.org/3/library/sys.html)


### Non-Python dependencies
- [MarcEdit](https://marcedit.reeset.net/) - Experimental - Functions in transform_marc_file.py can be called to run Validation and MarcBreaker functionality from the command line via the subprocess module. MarcEdit provides a [command-line tool](https://marcedit.reeset.net/cmarcedit-exe-using-the-command-line) as part of its functionality. Currently capable of validating or breaking mrc files. Applying MarcEdit task files has not been succesfully implemented in this repository.
This requires two environment variables:
- `CMARCEDIT_PATH` - the absolute path to cmarcedit.exe in MarcEdit installation.
- `MARCEDIT_RULES` - the absolute path to the MarcEdit rules file. 


## Scripts

### Current scripts

#### process_marc_file.py

**Steps**
- Start pipenv shell.
- Place a single MARC (.mrc) file in the `/input/load/mrc/` directory.
- Run `py process_marc_file.py` or `python process_marc_file.py`
- Enter output filename when prompted.

Takes a MARC file as input. Splits the records into parent and many record directories, then calls the API to retrieve missing identifiers and writes the records to the parent directory.
Iterates through the many records and performs the following:
- replaces 1xx, 260/264, 6xx, 7xx, 8xx from parent record.
- fixes indicators.
- fixes 655 trailing punctuation on $2 gmgpc subject headings.
- Generates a final merged MARC record in an output director with a MarcEdit validation report and MARC Text File (.mrk).
Requests user input for output filename and creates a MarcEdit validation report in the same directory.


### In development scripts 

#### run_call.py

Retrieves a list of MMS Ids supplied as a csv value in the environment variable MMS_IDS, writes the XML records to output directory, and retrieves a list of parent record MMS Ids.

**Required updates**
- requires further steps to retrieve parent records and perform record matching.

#### update_037.py

Script for updating accession numbers from another list. Takes a list with accession numbers and mms ids and uses pandas to manage record handling. 

- Takes an Excel spreadsheet as input.
- Gets accession numbers and identifiers from sheet.
- Makes API call to retrieve records
- Gets list of parent MMS Ids from the records
- Makes API call to retrieve unique records
- Checks accession numbers against parent records
    - Updates if whitespace is different to parent
- Writes exceptions to exceptions file and log.
- Updates files with matches with a valid 037.
- Tidies up MANY records based on data in parent records.
- Creates .mrc, .mrk, and validation reports for successful updates and exceptions.

## Supporting functions

These functions are not split in optimal ways so will need to be re-worked into more logical files.

#### shared_functions.py

Functions for splitting Marc records into `output/mrc/split/parent` and `output/mrc/split/many` directories for further processing and retrieving missing parent records not in the directory.

#### Api_call.py  

Contains functions to retrieve bibliographic records via the Alma API and writes the JSON response to file.
Validates MMS IDs based on State Library Victoria MMS Id stucture. This will need to be changed for other institutions.

Has unit tests.

#### extract_xml.py

Contains functions to read JSON file, retrieve bib XML, and fix header encoding.

Has unit tests.

#### xml_load_and_process.py

Functions that can be used to load Pymarc Record objects from MARCXML files. Also includes functions to replace fields from one record into another.  

Has unit tests.

#### get_parent_ids.py

Functions targeting data in the local field 950$p that represent relationship links between 'parent' records and 'many' records for digital items not described individually.

Has unit tests.

#### transform_marc_file.py

Functions that call `cmarcedit.exe` to perform validation and MARCBreaker tasks.

#### logger_config.py

Functions for configuring a logger. Used for testing individual scripts as part of development. When running all scripts the logfile writes to `logs/log_api_call.log`.

## Pyunit tests

The scrips include a number of pyunit tests and fixtures to improve future development of tests. Of interest:

### Fixtures

Fixtures are specified in `tests/conftest.py` to be used across different tests. Fixtures include:

- `temp_marc_file` - A path to a MARC file with multiple records.
- `setup_working_directory` - Creates a mirror directory in a temporary folder.
- `single_record` - A single Pymarc Record object.
- `field_replace_record` - Allows for a list of Pymarc Field objects to be passed to the `single_record` object for testing expected functionality.
    - Requires `@pytest.mark.parametrize("set_field_list", list_of_fields, indirect=["set_field_list"])` to configure the tests where `list_of_fields` is a list of one or more field objects submitted as a list.
- `get_validation_report` - An example MarcEdit validation report with errors to support development of parsing these reports in future.
- `missing_parents` - A copy of parent records for the records in the `temp_marc_file` fixture. In a live run these would be retrieved via the API.

