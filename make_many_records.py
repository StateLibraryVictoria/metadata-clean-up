import os
import pandas as pd
from copy import deepcopy
from sys import exit
from copy import deepcopy
from src.shared_functions import *
from src.xml_load_and_process import *
from src.get_parent_ids import *
from src.logger_config import *
from src.transform_marc_file import *


"""This process is intended to load a spreadsheet of digitised images, and use the parent record ID to generate a preliminary MARC record that can be bulk loaded into Alma to support digitising workflows.
"""

# setup workspace
setup_directories()

# clean up temporary files in workspace
#clear_temporary_files()

# load spreadsheet
location = os.path.join("input","load","excel")
for root, dir, files in os.walk(location):
    if len(files) == 0:
        print("No files staged in Excel staging area. Add files to /input/load/excel")
        sys.exit()
    elif len(files) > 1:
        print("Too many files staged in Excel staging area. Only stage one file at a time.")
        sys.exit()
    else:
        try:
            data = pd.read_excel(os.path.join(root, files[0]))
            print(f"Successfully loaded dataframe of shape: {data.shape}")
        except Exception as e:
            print(f"Error loaded Excel file to dataframe: {e}")

# Filter to MANY rows
df_many = data.loc[data['ONE MANY']=="MANY"]

# get unique parent ids
request_ids = []
id_count = {}
for id in df_many['Parent MMS ID']:
    if str(id) not in request_ids:
        request_ids.append(str(id))
        id_count.update({str(id): 1})
    else:
        total = id_count[str(id)] + 1
        id_count.update({str(id):total})
print(f"Found {len(request_ids)} unique parent MMS Ids.")
request_ids.sort()
# call Alma API to retrieve parent records
output_dir_parent = os.path.join("output", "mrc", "split", "parent")
"""try:
    get_missing_records([],request_ids,output_dir_parent)
except Exception as e:
    print(f"Error retriving records from API: {e}")"""

# Get fields from parent (do we add these to dataframe?)
fields_df = pd.DataFrame()
ids_series = pd.Series(request_ids)
fields_df['ids'] = ids_series
fields_df['parent_file'] = output_dir_parent + os.sep + ("record_" + fields_df['ids']+".mrc")
# define which tags correspond to which headers
get_fields_mapping = {"date_26xc":['260','264'],"extent":['300'], 'header_1xx':['100','110','111','130'],'contents_505':['505'], 'title_245':['245']}
required_headers = get_fields_mapping.keys()
# generate columns from keys
for field in required_headers:
    fields_df[field] = ""
"""fields_df['date_26xc'] = False
fields_df['date_008'] = False
fields_df['extent'] = False
fields_df['contents_505'] = False
fields_df['header_1xx'] = False
fields_df['title_245'] = False"""



# Create 008 date values.
for index, row in fields_df.iterrows():
    try:
        # Open file and add row based on date
        with open(row['parent_file'], 'rb') as pf:
            p_reader = pymarc.MARCReader(pf)
            for record in p_reader:
                print(record['001'].value())
                parent_rec = deepcopy(record)
                #parent_rec = many_record_cleanup(parent_rec, record)
                # iterate through columns
                for key in get_fields_mapping:
                    # get fields
                    fields = parent_rec.get_fields(*get_fields_mapping[key])
                    total = []
                    if key == "date_26xc":
                        try:
                            to_add = fields[0]['c']
                        except Exception as e:
                            print(f"Error adding date: {e}")
                    else:
                        for tag in fields:
                            as_string = tag.__str__()
                            total.append(as_string)
                        to_add = ";".join(total)
                    fields_df.at[index, key] = to_add
    except Exception as e:
         print(f"Failure in processing record {e}")

## add 008
given_dates = {}
dates_series = fields_df['date_26xc']
for item in dates_series:
    if item not in given_dates:
        item_transformed = date_to_008(item)
        given_dates.update({item:item_transformed})
for key in given_dates:
    dates_series = dates_series.replace(key, given_dates[key])
fields_df["date_008"] = dates_series

# fix simple 3xx
# use id_count dictionary
sliced = fields_df[['ids','extent']]
for key in id_count:
    count = id_count[key]
    extent = sliced.loc[sliced['ids'] == str(key), 'extent'].values[0]
    id_count.update({key: (count, extent)})

# replace 3xx extent where count is the same as 300$a
fields_df['count'], fields_df['updated_extent'] = "", ""
final_s = r"s( \(?.*\)? ?:\$b)"
extent_count = r"\$a(\d+)"
for key in id_count:
    count, extent = id_count[key]
    extent_query = re.findall(extent_count, extent)
    if extent_query[0] == str(count):
        replace_extent = extent.replace(f"$a{count}","$a1").replace("prints","print").replace("photographs","photograph").replace("s :$b"," :$b")
        print(extent)
        print(replace_extent)
## somehow get this back into the normal df. 

print(id_count)

"""
                date = parent_rec.get_fields('260','264')
                if len(date) == 1:
                    for field in date:
                        target = field['c']
                        if given_dates.get(target) == None:
                            fields_df['date_26xc'].replace(row['date_26xc'], target, inplace=True)
                            transformed = date_to_008(target)
                            fields_df['date_008'].replace(row['date_008'], transformed, inplace=True)
                            given_dates.update({target: transformed})
                        else:
                            fields_df['date_26xc'].replace(row['date_26xc'], target, inplace=True)
                            fields_df['date_008'].replace(row['date_008'], given_dates.get(target), inplace=True)
                extent = parent_rec.get_fields("300")
                record_count = id_count.get(parent_rec['001'].value())
                print(f"Processing extent for record {parent_rec['001'].value()}: ")
                print(f"Supplied records with this id: {record_count}")
                if len(extent) == 1 and extent[0]['a'].startswith(str(record_count)):
                    a_field = extent[0]['a'].replace(str(record_count), "1").replace("s :", " :").replace("prints","print")
                    print(a_field)
                    extent_copy = extent[0]
                    extent_copy['a'] = a_field
                    print(extent.value())
                    fields_df['extent'].replace(row['extent'], extent_copy.value(), inplace=True)
                else:
                    fields_df['extent'].replace(row['extent'], ";".join(extent), inplace=True)
                contents = parent_rec.get_fields("505")
                for item in contents:
                    item = item.value()
                if len(contents) > 0:
                    fields_df["contents_505"].replace(row["contents_505"], ";".join(contents), inplace=True)
                onexx = parent_rec.get_fields('100', '110', '111', '130')
                if onexx == 1:
                    print(onexx[0].value())
                    fields_df['header_1xx'].replace(row['header_1xx'], onexx[0].value(), inplace=True)
                else:
                    for item in onexx:
                        print(item.value())
                # tidy up records."""
df_many["Parent MMS ID"] = df_many["Parent MMS ID"].astype(str)
join_df = pd.merge(df_many, fields_df, left_on ='Parent MMS ID', right_on='ids', how='left')

print(join_df.head())
print(list(join_df))
print(join_df.size)
# write to output file
join_df.to_csv("parent_record_join_output.csv")

# Get specific fields from parent. [001, 1xx, 260/264, 300, ]
# Write them into the pandas dataframe
	# Generate 008
	# Generate 300
# Write to MARC file.
# Open in MarcEdit and apply task file.