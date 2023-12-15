# Metadata Clean-up Project

A Code Club project to create some tools to help clean-up metadata in the Library's catalogue systems

# Pseudocode  
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

# Alma API

Alma provides documentation of the REST APIs on their website: [link](https://developers.exlibrisgroup.com/alma/apis/). They also provide an [API Console](https://developers.exlibrisgroup.com/console/) for testing. Based on initial investigations in the *Bibliographic Records and Invventory* section it appears that responses can be returned in either XML or JSON. XML appears to contain complete bibliographic records, while JSON contains only some fields.

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
