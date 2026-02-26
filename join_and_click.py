import json
import logging
from telethon.sync import TelegramClient, events
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from time import sleep
import os
import sys
import random



# Setup basic logging
logging.basicConfig(level=logging.ERROR)

# Read configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r') as file:
    config = json.load(file)

group_url = config['join_group']  # The group's username or invite link

# Print location and list of group links
print(f"[INFO] Group link(s) location: {config_file}, key: 'join_group'")
if isinstance(group_url, list):
    print("[INFO] Full group link list:")
    for g in group_url:
        print(f"  - {g}")
else:
    print(f"[INFO] Single group link: {group_url}")

# Define the path for session files
root_path = os.path.dirname(os.path.abspath(__file__))
folder_session = os.path.join(root_path, 'telethon_sessions')



# Function to join and click button in a group
async def join_and_click(client, group_url):
    # Join group using the correct method for the link type
    if group_url.startswith("https://t.me/+") or group_url.startswith("https://t.me/joinchat/"):
        invite_code = group_url.split("/")[-1].replace("+", "")
        await client(ImportChatInviteRequest(invite_code))
        print(f"Joined (invite) {group_url}")
    else:
        await client(JoinChannelRequest(group_url))
        print(f"Joined {group_url}")
    sleep(5)

    # Then, get the most recent message in the group
    messages = await client.get_messages(group_url, limit=1)
    if not messages:
        print("No messages found.")
        return

    # Assuming the latest message has a button, get its data
    latest_message = messages[0]
    button_data = latest_message.buttons[0][0].data if latest_message.buttons else None
    if not button_data:
        print("No buttons found. Probably we are already a member of the chat.")
        #it will send a test message but this needs to be shilling, because we only send the test message to make sure we joined, but if we are sending messages any, we might as well shill
        test_message = "WHATS UP"
        #await client.send_message(group_url, test_message)
        print(f"we aren't sending a message right now")
        return
    
    # Click the button by sending a GetBotCallbackAnswerRequest
    await client(GetBotCallbackAnswerRequest(
        peer=group_url,
        msg_id=latest_message.id,
        data=button_data
    ))
    print("Button clicked.")


# Main loop to go through all accounts
for phone in config['accounts']:
    # Prefer telethon_sessions/{phone}.session if it exists
    telethon_session = os.path.join('telethon_sessions', f'{phone}.session')
    session_session = os.path.join(folder_session, phone)
    if os.path.exists(telethon_session):
        session_file = os.path.join('telethon_sessions', phone)
    else:
        session_file = session_session
    print(f"attempting to join with {phone}\n\n")
    # Create and start the Telegram client for each account using the session file
    client = TelegramClient(session_file, config['api_id'], config['api_hash'])

    with client:
        client.loop.run_until_complete(join_and_click(client, group_url))
        sleep_time1 = random.randint(300, 420)
        print(f"Sleeping for {sleep_time1}")
        sleep(sleep_time1)

