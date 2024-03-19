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

### Api call  

- [json](https://docs.python.org/3/library/json.html)
- [requests](https://requests.readthedocs.io/en/latest/)
- [sys](https://docs.python.org/3/library/sys.html)

Requires a `.env` file containing local variables. 

### XML extraction

- [json](https://docs.python.org/3/library/json.html)

### Load XML to Pymarc

- [pymarc](https://pymarc.readthedocs.io/en/latest/)


### Future scripts  

- [pymarc](https://pymarc.readthedocs.io/en/latest/)

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

## MarcEdit command line tool

MarcEdit provides a [command-line tool](https://marcedit.reeset.net/cmarcedit-exe-using-the-command-line) as part of its functionality. This is proposed to be investigated as an option for simplifying MARC validation tasks, once a working proof of concept for replacing the parts of the workflow that currently require OpenRefine.

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