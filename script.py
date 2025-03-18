from email import parser
from lxml import etree
import csv
import json
import re
from dateutil import parser as date_parser
from pytz import timezone
from collections import defaultdict


def convert_date_format(input_date, input_type, output_timezone="Africa/Cairo"):
    """
    Converts an input date to match the format of the input_type.

    :param input_date: The date string to convert.
    :param input_type: A string representing the desired format to match.
    :param output_timezone: The desired timezone for conversion (default is "Africa/Cairo").
    :return: The formatted date string matching the input_type's format.
    """
    try:
        # Define regex patterns
        naive_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$'  # Example: 2006-11-29T19:20:00
        timezone_aware_pattern = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'  # Example: 2003-08-09T03:18:37+03:00

        # Parse the input date dynamically
        dt = date_parser.parse(input_date)
        tz = timezone(output_timezone)

        # Determine the date type using regex and process accordingly
        if re.match(timezone_aware_pattern, input_type):
            print(f"Detected timezone-aware format for input_type: {input_type}")
            # Adjust timezone-aware datetime
            if dt.tzinfo is None:
                dt = tz.localize(dt)  # Add timezone if missing
            else:
                dt = dt.astimezone(tz)
            # Format to match input_type
            formatted_date = dt.strftime('%Y-%m-%dT%H:%M:%S%z')
            # Insert colon in timezone part to match input_type
            formatted_date = formatted_date[:-2] + ":" + formatted_date[-2:]
        elif re.match(naive_pattern, input_type):
            print(f"Detected naive format for input_type: {input_type}")
            # Remove timezone info for naive datetime
            if dt.tzinfo is not None:
                dt = dt.replace(tzinfo=None)  # Strip timezone
            # Format to match input_type
            formatted_date = dt.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            raise ValueError(f"Input type '{input_type}' does not match any known date patterns.")

        return formatted_date

    except Exception as e:
        print(f"Error converting date '{input_date}': {e}")
        raise

def parse_schema(schema_path,key_dates):
    schema_tree = etree.parse(schema_path)
    root = schema_tree.getroot()

    namespace = {"max": "http://www.ibm.com/maximo"}
    main_element = root.tag.split("}")[1]
    object_structure = main_element.replace("Create", "")

    main_set = root.find(f".//max:{object_structure}Set", namespaces=namespace)
    if main_set is None:
        raise ValueError(f"No main set (e.g., <max:{object_structure}Set>) found in the schema.")

    main_object = None
    relationships = {}
    date_pattern_with_tz = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\+\-]\d{2}:\d{2}'
    date_pattern_without_tz = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
    def extract_relationships(element, parent):
        
        for child in element:
            tag = child.tag.split("}")[1]
            if re.match(date_pattern_with_tz, child.text):
                print("the tag name that is matched the date pattern",tag)
                print("the value is ",child.text)
                print("the parent is ",parent)
                key_dates[tag] = (child.text)
            elif re.match(date_pattern_without_tz, child.text):
                print("the tag name that is matched the date pattern",tag)
                print("the value is ",child.text)
                print("the parent is ",parent)
                key_dates[tag] = (child.text)
              
            if "relationship" in child.attrib:
                if parent not in relationships:
                    relationships[parent] = []
                #check if the value of the tag match the regex then add the tag name as key to key_dates map and the value be the tag value
              
                relationships[parent].append(tag)

            extract_relationships(child, tag)

    for index, child in enumerate(main_set, start=1):
        tag = child.tag.split("}")[1]
        if re.match(date_pattern_with_tz, child.text):
            print("the tag name that is matched the date pattern",tag)
            print("the value is ",child.text)
            print("the parent is ",parent)
            key_dates[tag] = (child.text)
        elif re.match(date_pattern_without_tz, child.text):
            print("the tag name that is matched the date pattern",tag)
            print("the value is ",child.text)
            print("the parent is ",parent)
            key_dates[tag] = (child.text)
        if index == 1:
            main_object = tag
        elif "relationship" in child.attrib:
            if main_object not in relationships:
                relationships[main_object] = []
           #check if the value of the tag match the regex then add the tag name as key to key_dates map and the value be the tag value
          
            relationships[main_object].append(tag)

        extract_relationships(child, tag)

    return object_structure, main_object, relationships

def generate_root(object_name, csv_path, key_attrs, key_to_root_map, root_map_itself, main_key,key_dates):
    """
    Generates the root elements for the parent data from the CSV.

    :param object_name: Name of the object for the root elements.
    :param csv_path: Path to the parent CSV file.
    :param key_attrs: List of key attributes used for mapping.
    :param key_to_root_map: Mapping from keys to the corresponding root.
    :param root_map_itself: Map of main key values to their corresponding XML elements.
    :param main_key: Keys that define the main object mapping.
    """
    with open(csv_path, 'r',encoding='latin-1') as csvfile:
        reader = csv.DictReader(csvfile)
        main_keys = main_key
        for row in reader:
            main_key_value = ""
            root = etree.Element(object_name)

            # Sort attributes before creating XML elements
            for attr_name in main_keys:
                for attr_name1 in sorted(row.keys()):  # Sort attribute names
                    if attr_name == attr_name1:
                        main_key_value += row[attr_name1].strip().upper()

            for attr_name in row.keys():  # Sort attribute names
                value = row[attr_name]
                #i want here to check if any attribute name is in a key_dates a date and if it is then convert it to iso format    
                if attr_name in key_dates:
                    print("the date attribute is ",attr_name)
                    print("the date value is ",value)
                    print("the date format is ",key_dates[attr_name])
                    #check if the value is not empty or null first
                    if value.strip() != "" and value.strip() != "NULL":
                        value = convert_date_format(value,key_dates[attr_name])
                child = etree.SubElement(root, attr_name)
                child.text = value.strip() if value.strip().upper() != "NULL" else ""

            # print("The main_key_value:", main_key_value)
            # print("key_attrs:", key_attrs)


            # Map each key value to the root
            for key1 in key_attrs:
                key_value=""
                for key in key1.split("+"):
                    key_value += row.get(key, "").strip().upper()
                if key_value:
                    # print(f"Mapping key {key_value} to root {root}")
                    key_to_root_map[key_value] = main_key_value
                    root_map_itself[main_key_value] = root


def update_xml_with_csv(csv_file_path, object_name, key_attr, key_to_root_map, root_map_itself,key_dates):
    """
    Updates the XML with rows from the CSV for child relationships.

    :param csv_file_path: Path to the CSV file.
    :param object_name: The name of the object to be added to the XML.
    :param key_attr: The attribute name used as the key for this relationship.
    :param key_to_root_map: Mapping from keys to the corresponding root.
    :param root_map_itself: Map of main key values to their corresponding XML elements.
    """
    with open(csv_file_path, 'r',encoding='latin-1') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key_value = ""
            # Generate key value from attributes
            for key in key_attr.split("+"):
                key_value += row.get(key, "").strip().upper()
            if not key_value:
                #print(f"Skipping row: Missing key value for {key_attr}")
                continue

            # Create the relationship object
            child = etree.Element(object_name)
            # Sort attributes before creating XML elements
            for attr_name in sorted(row.keys()):  # Sort attribute names
                value = row[attr_name]
                #i want here to check if any attribute name is in a key_dates a date and if it is then convert it to iso format
                if attr_name in key_dates:
                    # print("the date attribute is ",attr_name)
                    # print("the date value is ",value)
                    # print("the date format is ",key_dates[attr_name])
                    if value.strip() != "" and value.strip() != "NULL":
                        value = convert_date_format(value,key_dates[attr_name])
                attr_child = etree.SubElement(child, attr_name)
                attr_child.text = value.strip() if value.strip().upper() != "NULL" else ""

            # Match the relationship to the main root
            matched_root_key = key_to_root_map.get(key_value)
            if matched_root_key:
                parent_root = root_map_itself.get(matched_root_key)
                if parent_root:
                    parent_root.append(child)
                    print(f"Added {object_name} to root {matched_root_key}")
            # else:
            #     print(f"No match found for key {key_attr}={key_value}. Skipping.")

                     
def update_tag_in_xml(root_map, tag_name, attribute_name, match_value, new_tag_structure_func):
    """
    Iterates through XML elements in a map, finds a specific tag by name,
    checks an attribute value (or child element value), and updates the tag if a match is found.

    :param root_map: A dictionary where keys are identifiers and values are etree.Element objects.
    :param tag_name: Name of the tag to search for.
    :param attribute_name: Attribute name(s) or child tags to check (can be a list for composite keys).
    :param match_value: Value to match with the attribute(s) or child element values.
    :param new_tag_structure_func: Function to generate the new tag structure.
    """
    for key, value_map in root_map.items():
        print(f"Processing element with key: {key}")
        
        # Find all children with the specified tag name
        for child in value_map.findall(f".//{tag_name}"):
            print(f"Processing child: {etree.tostring(child, pretty_print=True, encoding='unicode')}")
            
            # Build composite attribute/child element values
            attribute_values = ''
            for attribute_val in attribute_name:
                # Check as an attribute
                attr_value = child.get(attribute_val, None)
                
                if attr_value is None:
                    # If not found as an attribute, check as a child element
                    attr_value = child.findtext(attribute_val, default="")
                
                # print(f"Checking attribute/child: {attribute_val}, Value: {attr_value}")
                attribute_values += attr_value  # Concatenate the value
            
                print(f"Composite attribute/child value: {attribute_values}")
            
            # Check if the composite value matches
            if attribute_values == match_value:
                print(f"Found matching tag: <{tag_name}> with {attribute_name}={match_value}")
                
                # Generate a new structure for the matching tag
                new_tag = new_tag_structure_func
                print(f"Processing new_tag: {etree.tostring(new_tag, pretty_print=True, encoding='unicode')}")

                # Replace the old child with the new one
                parent = child.getparent()
                print("the parent is ", parent)
                if parent is not None:
                    parent.replace(child, new_tag)
                    print(f"Updated tag <{tag_name}> with additional children.")


    
   # Parse schema

schema_path = input("Enter the schema path without extension: ")
schema_path = "/etc/" + schema_path + ".xml"
key_dates={}
object_structure, main_object, heirarchy = parse_schema(schema_path,key_dates)

print(f"Parsed object structure: {object_structure}")
print(f"Main object: {main_object}")
print(f"heirarchy: {heirarchy}")


key_to_root_map = {}
root_map_itself = defaultdict(list)
#create root of etree but make it null for now
Root1 = etree.Element(main_object)
# Process child relationships

# Path to your JSON file
json_file_path = "/etc/hi.json"

# Read JSON data
key_attrs=[]
with open(json_file_path, 'r') as json_file:
    data = json.load(json_file)

# for parent, children in heirarchy.items():  # Properly access parent and child list
#     # Loop through the list of children
#     for child in children:
#         # Form the key attribute as "parent+child"
#         key_attr = parent + "+" + child
#         print(f"key_attr: {key_attr}")
        
#         # Fetch the data from the JSON mapping
#         key_attr_values = data.get(key_attr, [])
#         print(f"key_attr_values: {key_attr_values[0]}")
#         if(key_attrs.count(key_attr_values[0])>0):
#             continue
#         key_attrs.append(key_attr_values[0])  # Add to
# Process each relationship
itr=0
for parent, children in heirarchy.items():
    idx=0
    itr=itr+1
    root_map_itself={}
    key_to_root_map={}
    list_csv_files = []
    print("my children are ", children)
    csv_main_name = input(f"Enter the CSV file for the main object '{parent}' (without extension): ")
    csv_main_path = f"/etc/{csv_main_name}.csv"
    for child in children:         
        csv_name = input(f"Enter the CSV file for {idx+1} relationship '{child}' (without extension): ")
        list_csv_files.append(f"/etc/{csv_name}.csv")
        idx=idx+1
          # Form the key attribute as "parent+child"
        key_attr = parent + "+" + child
        print(f"key_attr: {key_attr}")
        
        # Fetch the data from the JSON mapping
        key_attr_values = data.get(key_attr, [])
        print(f"key_attr_values: {key_attr_values[0]}")
        if(key_attrs.count(key_attr_values[0])>0):
            continue
        key_attrs.append(key_attr_values[0])  # Add to  
    idx=0
    for child in children:
        # Construct key_attr without braces
        key_attr = f"{parent}+{child}"  # Match new JSON key format
        print(f"Generated key_attr: {key_attr}")
        csv_path=list_csv_files[idx]
        print("csv path = ", csv_path)
        # Fetch key attributes from JSON
        main_key = data.get(parent, [])  # Fetch main object keys
        print("key attrs = ", key_attrs)
        key_relation=data.get(key_attr, [])
        key_attr_child=key_relation[1]
        print("main key = ", main_key)
        main_key_temp = []
        for key in main_key[0].split("+"):
            #take the string and split it using +
            main_key_temp.append(key)
            print("main key temp = ", main_key_temp)
        main_key = main_key_temp
        # If keys are empty, print warning
        if not key_attrs:
            print(f"Warning: No key attributes found for {key_attr}. Check JSON file.")

        if not main_key:
            print(f"Warning: No main keys found for {parent}. Check JSON file.")
        if idx==0:
            # Call generate_root
            generate_root(parent, csv_main_path, key_attrs, key_to_root_map, root_map_itself, main_key,key_dates)

        # Call update_xml_with_csv
        update_xml_with_csv(csv_path, child, key_attr_child, key_to_root_map, root_map_itself,key_dates)        
        if(itr==1):
            Root1=root_map_itself
            #print("Root1=",Root1)
            print("Root1=",Root1)
        else:
            #update the Root1 with the root_map_itself by matching the keys
                #get the heirarchy idx
        
            #iterate through the root_map_itself

            for key, value in root_map_itself.items():
                print ("root_map_itself.items()=",etree.tostring(value, pretty_print=True, encoding='unicode'))
                print("the key is ",key)
                print("the value is ",value)
                update_tag_in_xml(Root1, parent, main_key_temp,key, value)
        #generate XML and print
        temp = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Sync{object_structure} xmlns="http://www.ibm.com/maximo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <{object_structure}Set>"""
        temp1 = f"""</{object_structure}Set>
        </Sync{object_structure}>"""
        file_path = f"/etc/{object_structure}_output.xml"
        with open(file_path, "w") as f:
            main_xml = ""
            for root in Root1.values():
                xml_string = etree.tostring(root, pretty_print=True, encoding='utf-8').decode()
                main_xml += xml_string
            final_xml = temp + main_xml + temp1 
            f.write(final_xml)
        print("XML generation complete. Saved to", file_path)   
        idx=idx+1
       
# # Generate the final XML
# temp = f"""<?xml version="1.0" encoding="UTF-8"?>
# <Sync{object_structure} xmlns="http://www.ibm.com/maximo" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
#   <{object_structure}Set>"""
# temp1 = f"""</{object_structure}Set>
# </Sync{object_structure}>"""

# file_path = f"C:/Users/dada/Downloads/{object_structure}_output.xml"
# with open(file_path, "w") as f:
#     main_xml = ""
#     for root in Root1.values():
#         xml_string = etree.tostring(root, pretty_print=True, encoding='utf-8').decode()
#         main_xml += xml_string
#     final_xml = temp + main_xml + temp1
#     f.write(final_xml)

# print("XML generation complete. Saved to", file_path)