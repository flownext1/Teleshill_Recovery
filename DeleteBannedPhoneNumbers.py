import json
import os
import sys

# Read config file from command line argument or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'

# Load the content of config.json
with open(config_file, 'r') as config_file_obj:
    config_data = json.load(config_file_obj)

# Load the content of banned.json
if not os.path.exists('banned.json'):
    print("No banned.json file found. No banned numbers to delete.")
    exit(0)

with open('banned.json', 'r') as banned_file:
    banned_data = json.load(banned_file)

# Extract banned values
banned_values = set(banned_data['banned'])

def remove_banned_values(obj, banned_values):
    if isinstance(obj, dict):
        return {k: remove_banned_values(v, banned_values) for k, v in obj.items()}
    elif isinstance(obj, list):
        new_list = []
        for item in obj:
            if item in banned_values:
                print(f"Deleting banned value: {item}")
            else:
                new_list.append(remove_banned_values(item, banned_values))
        return new_list
    else:
        return obj


# Remove the banned values
config_data = remove_banned_values(config_data, banned_values)

# Save the modified config
with open(config_file, 'w') as config_file_obj:
    json.dump(config_data, config_file_obj, indent=4)

print(f"Updated {config_file} after removing banned values.")