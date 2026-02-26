import random
import json

# Load the data from the dictionary.json file
with open('dictionary.json', 'r') as file:
    data = json.load(file)

# Extract the arrays of terms and bip39_words from the loaded data
terms = data['terms']
bip39_words = data['bip39_words']

# Generate 100 different unique usernames
unique_usernames = set()
while len(unique_usernames) < 100:
    random.seed()
    random.seed()
    random.seed()
    random_term = random.choice(terms)

    # Capitalize the entire random_term 10% of the time
    if random.random() < 0.1:
        random_term = random_term.upper()

    random_bip39_word = random.choice(bip39_words)
    
    # Insert an underscore 5% of the time between term and bip39_word
    if random.random() < 0.05:
        username = random_term + '_' + random_bip39_word
    else:
        username = random_term + random_bip39_word

    # Capitalize the entire username 5% of the time
    if random.random() < 0.05:
        username = username.upper()

    # Append 2 random numbers at the end 10% of the time
    if random.random() < 0.25:
        random_numbers = ''.join(random.choices('0123456789', k=2))
        username += random_numbers

    unique_usernames.add(username)

# Convert the set of usernames to a list
usernames_list = list(unique_usernames)

# Create a dictionary with the 'names' key
output_dict = {"names": usernames_list}

# Output the usernames in JSON format to names.json
with open('ShittyNames.json', 'w') as output_file:
    json.dump(output_dict, output_file, indent=2)

print("Usernames generated and saved to ShittyNames.json")
