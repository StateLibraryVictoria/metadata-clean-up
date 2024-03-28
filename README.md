# Metadata Clean-up Project

A Code Club project to create some tools to help clean-up metadata in the Library's catalogue systems.

# Getting started

## Dependencies

        Use this space to track additional libraries relied on in the code.

### Whole project
- [logging](https://docs.python.org/3/library/logging.html)
- [os](https://docs.python.org/3/library/os.html)
- [pipenv](https://pipenv.pypa.io/en/latest/)
- [pytest](https://docs.pytest.org/en/8.0.x/)
- [json](https://docs.python.org/3/library/json.html)
- [requests](https://requests.readthedocs.io/en/latest/)
- [sys](https://docs.python.org/3/library/sys.html)
- [subprocess](https://docs.python.org/3/library/subprocess.html)
- [pymarc](https://pymarc.readthedocs.io/en/latest/)

### Non-Python dependencies
- [MarcEdit](https://marcedit.reeset.net/) - Experimental - Functions in transform_marc_file.py can be called to run Validation and MarcBreaker functionality from the command line via the subprocess module. MarcEdit provides a [command-line tool](https://marcedit.reeset.net/cmarcedit-exe-using-the-command-line) as part of its functionality. Currently capable of validating or breaking mrc files. Applying MarcEdit task files has not been succesfully implemented in this repository.
This requires two environment variables:
- `CMARCEDIT_PATH` - the absolute path to cmarcedit.exe in MarcEdit installation.
- `MARCEDIT_RULES` - the absolute path to the MarcEdit rules file. 


## Scripts

### Runnable scripts

#### process_marc_file.py

Takes a MARC file as input. Splits the records into parent and many record directories, then calls the API to retrieve missing identifiers and writes the records to the parent directory.
Iterates through the many records and updates the 100, 110, 260 and 264, overwriting the split many records with the new values and creating a logfile of changes.

**Next steps**  
- output updated records to single file
- validate with MarcEdit
- create unit tests for related processes

#### run_call.py

Retrieves a list of MMS Ids supplied as a csv value in the environment variable MMS_IDS, writes the XML records to output directory, and retrieves a list of parent record MMS Ids.

**Required updates**
- requires further steps to retrieve parent records and perform record matching.

### Supporting functions

These functions are not split in optimal ways so will need to be re-worked into more logical files.

#### shared_functions.py

Functions for splitting Marc records into `output/mrc/split/parent` and `output/mrc/split/many` directories for further processing and retrieving missing parent records not in the directory.

**Requires unit test development**

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

#### logger_config.py

Functions for configuring a logger. Used for testing individual scripts as part of development. When running all scripts the logfile writes to `logs/log_api_call.log`.

## Deliverables

1. Alma API call: Takes a list of MMS Ids and returns JSON records containing up to 100 MARCXML records.
2. XML extraction: Takes the JSON response and exports each XML record to its own file.
3. Load XML: Loads MARCXML to Pymarc record objects.
4. Transformations:
    - Get parent MMS ID: Gets valid MMS Ids from the 950 $p field. Identifiers can be written to file or used as a lsit to call the API.
    - Fix 655 gmgpc genre term headings - remove trailing period.
    - Copy specified fields from parent record to child.
5. Output files as .mrc files.
- Unit tests (ongoing)


# Early plan 

## Pseudocode  
Updated pseudocode migrated from kaggle notebook

        # Metadata cleanup project  
        # Get child item  
        # Find parent item of child  
            # Get parent item of child  
        # Compare field 264  
            # If match do nothing  
            # If blank in parent do nothing  
            # Else change child to parent value  
                # Alternative: suggest update to human user and 
                               user inputs confirmation

## Alma API

Alma provides documentation of the REST APIs on their website: [link](https://developers.exlibrisgroup.com/alma/apis/). They also provide an [API Console](https://developers.exlibrisgroup.com/console/) for testing. Based on initial investigations in the *Bibliographic Records and Invventory* section it appears that responses can be returned in either XML or JSON. XML appears to contain complete bibliographic records, while JSON contains only some fields.