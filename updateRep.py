'''
Tool for updating representation properties. Supports updating any properties that support PUT (see https://developers.exlibrisgroup.com/alma/apis/docs/xsd/rest_representation.xsd/?tags=PUT for details).
'''

import sys
import requests
import json
from datetime import datetime


def datestamp(ds):
	now = datetime.now()
	date_time = now.strftime("%m/%d/%Y, %H:%M:%S")
	stamp = "\n" + "-" * 25 + ds + date_time + "-" * 25 + "\n"
	return stamp

def report(status):
	if status == "success":
		if logfile:
			f.write(log + " - match, fixed\n")
		else:
			print(log + " - match, fixed")
	elif status == "fail":
		if logfile:
			f.write(putrep.text)
		else:
			print(putrep.text)	
	elif status == "skip":
		if logfile:
			f.write(log + " - no match, skipped\n")
		else:
			print(log + " - no match, skipped")



	
baseurl = "https://api-na.hosted.exlibrisgroup.com/almaws/v1/bibs/"

apikey = input ("API Key: ")

# check API key
headers = {
        "Authorization": "apikey " + apikey, 
		"content-type":"application/json", 
		"Accept":"application/json"}
sys.stdout.write("Checking API Key... ")
testapi = requests.post(baseurl + "test", headers=headers)
if testapi.status_code == 400:
	print("\nInvalid API Key - please confirm key has r/w permission for /bibs",)
	sys.exit()
elif testapi.status_code != 200:
	sys.stdout.write("Error\n",)
	sys.exit()
else:
	sys.stdout.write("OK\n")

# get input
list = input ("Location of bibs list: ")
logfile = input ("Logfile (leave empty for standard output): ").strip()
property = input ("Property to update: ").lower()
oldval = input ("Old Value ('*' for 'any'): ")  
newval = input ("New Value: ")  
confirm = input ("Replace '" + oldval + "' with '" + newval + "' for property '" + property +"'? (Y/N)") 
if confirm != "Y":
	print("Exiting")
	sys.exit()
else:
	print("\n Running... \n")

		
if logfile:
	try:
		f = open(logfile, 'a+')
		f.write(datestamp(" Start: "))
		f.write("Replacing '" + oldval + "' with '" + newval + "' for property '" + property +"'\n\n")
	except IOError:
		print("Cannot open log file " + logfile)
		sys.exit()

try:
	with open(list) as fp:
		line = fp.readline()
		mmsid_cnt = 1
		reps_fixed = 0
		reps_skipped = 0
		errors = 0
		doupdate = False
		
		# read mmsids from list
		while line:
			bib = line.strip()    
			url = baseurl + bib + "/representations/"
			getreps = requests.get(url, headers=headers)
			json_reps = getreps.json()		
			
			# read reps from bib
			for rep in json_reps["representation"]: 
				getrep = requests.get(rep["link"], headers=headers)
				json_rep = getrep.json()
				log = "MMS ID: " + bib + " representation ID: " + json_rep["id"]
				# handle rep object properties (active, usage_type, library, access_rights_policy_id)
				if "value" in json_rep[property] and ((json_rep[property]["value"] == oldval) or (json_rep[property]["value"] != newval and oldval =='*')): 
					json_rep[property]["value"] = newval
					doupdate = True
				# handle other rep properties
				elif "value" not in json_rep[property] and (json_rep[property] == oldval or (json_rep[property] != newval and oldval =='*')):
					json_rep[property] = newval
					doupdate = True
				if doupdate:					
					# update
					putrep = requests.put(rep["link"], data=json.dumps(json_rep), headers=headers)
					if putrep.status_code != 200:
						report("fail")						
						errors +=1
					else:
						report("success")						
						reps_fixed +=1
				else:
					report("skip")						
					reps_skipped +=1			
			line = fp.readline()
			mmsid_cnt += 1
			
except IOError:
	print("Cannot find file list " + list)
	sys.exit()

	
# summary		
summary = "\n Number of fixed representations:   " + str(reps_fixed) + "\n Number of skipped representations: " + str(reps_skipped) + "\n Number of errors:"+ " " * 18 + str(errors)
print(summary)
if logfile:
	f.write(summary)
	f.write(datestamp(" End: "))
	f.close()
	print("\n See details in " + logfile)
	