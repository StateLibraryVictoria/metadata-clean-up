# Metadata Clean-up Project

A Code Club project to create some tools to help clean-up metadata in the Library's catalogue systems

# Getting started

## Dependencies

        Use this space to track additional libraries relied on in the code.

## Deliverables

- Alma API call
    - Confirm regarding API usage, investigate developing in Sandbox.
    - Potential packages: Requests [Documentation](https://requests.readthedocs.io/en/latest/)
        - Functions Kaggle notebook has a code snippit with Request library use.
        - Normally return JSON data.
        - Alma developer network
    - Function for access token: Authentication (.env variables)
        - Send a request with a key
        - Returns access token
    - Function to get record
    - Test record set
- Script that parses the child records and outputs a list of parent MMS IDs
- Second API call set to retrieve parent records
- Script that transforms the pulls the data together and performs transformations
- Unit tests

## Deliverable 1 - API call  
0. Organise access key
1. Function for access token
2. Functions for GET request
3. Output

# Early plan 

## Pseudocode  
Pseudocode migrated from kaggle notebook. Created October 31.

        #Metadata cleanup project  
        #Get child item  
        #Find parten item of child  
        #Get parent item of child  
        #Compare field 264  
        #If match do nothing  
        #If blank in parent do nothing  
        #Else change child to parent value  
        #Alternative, to get suggestion of change, and deny/confirm, instead of going ahead with change  

## Alma API

Alma provides documentation of the REST APIs on their website: [link](https://developers.exlibrisgroup.com/alma/apis/). They also provide an [API Console](https://developers.exlibrisgroup.com/console/) for testing. Based on initial investigations in the *Bibliographic Records and Invventory* section it appears that responses can be returned in either XML or JSON. XML appears to contain complete bibliographic records, while JSON contains only some fields.

## Requests - Python Library

[Documentation](https://requests.readthedocs.io/en/latest/)

Library for writing HTTP/1.1 requests. 

## Alma API request  
Draft code retrieved using Chat-GPT.


        import requests  

        # Replace these variables with your Alma API key and institution's Alma API endpoint URL
        api_key = 'YOUR_ALMA_API_KEY'
        base_url = 'https://api-eu.hosted.exlibrisgroup.com'  # Update with your institution's endpoint

        # MMS ID of the record you want to retrieve
        mms_id = 'REPLACE_WITH_YOUR_MMS_ID'

        # Endpoint for retrieving a MARC record by MMS ID
        endpoint = f'{base_url}/almaws/v1/bibs/{mms_id}'

        # Prepare the headers with your API key
        headers = {
            'Authorization': f'apikey {api_key}',
            'Accept': 'application/xml'  # You can specify 'application/json' if you prefer JSON response
        }

        # Make the GET request to retrieve the MARC record
        response = requests.get(endpoint, headers=headers)

        if response.status_code == 200:
            marc_record = response.text
            # Do something with the MARC record, for example, print it
            print(marc_record)
        else:
            print(f"Failed to retrieve MARC record. Status code: {response.status_code}")
            print(f"Response: {response.text}")

