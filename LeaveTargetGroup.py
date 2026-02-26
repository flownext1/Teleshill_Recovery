import json
import logging
import os
import sys
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import LeaveChannelRequest

# Setup basic logging
logging.basicConfig(level=logging.ERROR)

# Read configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r') as file:
    config = json.load(file)

group_target = config['leave_group']  # The target group's username or invite link

# Define the path for session files
root_path = os.path.dirname(os.path.abspath(__file__))
folder_session = os.path.join(root_path, 'telethon_sessions')

# Function to leave the target group
async def leave_group(client, group_target):
    try:
        await client(LeaveChannelRequest(group_target))
        print(f"Left the group {group_target}")
    except Exception as e:
        print(f"Could not leave the group {group_target}: {e}")

# Main loop to go through all accounts
for phone in config['accounts']:
    # Define the session file path for each account
    session_file = os.path.join(folder_session, phone)  # Assuming session file name is the phone number

    # Create and start the Telegram client for each account using the session file
    client = TelegramClient(session_file, config['api_id'], config['api_hash'])
    print(f"\n\nattempting to leave {group_target} with {phone}\n\n")
    with client:
        client.loop.run_until_complete(leave_group(client, group_target))
