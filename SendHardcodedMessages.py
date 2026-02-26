import json
import logging
from telethon.sync import TelegramClient
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

# Print location and list of degen groups
print(f"[INFO] Degen group list location: {config_file}, key: 'send_ca_group'")
group_url = config['send_ca_group']
if isinstance(group_url, list):
    print("[INFO] Full degen group list:")
    for g in group_url:
        print(f"  - {g}")
else:
    print(f"[INFO] Single degen group: {group_url}")

root_path = os.path.dirname(os.path.abspath(__file__))
folder_session = os.path.join(root_path, 'telethon_sessions')
test_messages = [ "Dragon's the name of the game this year, yeah? Been swingin' this coin, right, and I'm tellin' ya, it's 5x returns every single week for months. Just saw it dip and rocket right back. You know it's listed on CMC. 🐲DRAGON🐲 Peep this SOLANA CA: 12FvihLoAzTtaA98YVuErGftCXtoc83t3YFk4WdKK79T", "nice find thanks",
    "Year of the Dragon's lit, folks. Been playin' this coin, making a sweet 5x every week for a while. Just bounced off the low - classic. It's up on CMC, check it. 🐲DRAGON🐲 SOLANA CA here: 12FvihLoAzTtaA98YVuErGftCXtoc83t3YFk4WdKK79T", "hell yea bro",
    "Heads up, Year Of The Dragon's where it's at. This coin? Been swingin’ it for profits, like 5x each week, past few months. Just hit bottom and soared. Already on CMC. 🐲DRAGON🐲 SOLANA CA: 12FvihLoAzTtaA98YVuErGftCXtoc83t3YFk4WdKK79T", "ANOTHER DRAGON COIN? UGH TAKE MY MONEY",
    "So, Year Of The Dragon, right? This coin’s my golden goose, no kidding – 5x a week, been at it for months. Watched it plummet and rise. It's listed, yeah, on CMC. 🐲DRAGON🐲 SOLANA CA, note it down: 12FvihLoAzTtaA98YVuErGftCXtoc83t3YFk4WdKK79T", "LFG",
    "Check this - Year Of The Dragon’s the buzz. Swingin’ this coin's been a wild ride, netting me a solid 5x weekly for a good stretch. Just did the dip and upswing dance. It’s on CMC too. 🐲DRAGON🐲 SOLANA CA for ya: 12FvihLoAzTtaA98YVuErGftCXtoc83t3YFk4WdKK79T"]


# Function to send a test message in a group
async def send_message(client, group_url, test_message):
    # Send the designated test message to the group
    await client.send_message(group_url, test_message)
    
    time_to_sleep = random.randint(1200, 3600)
    print(f"Test message sent: {test_message}\n\nSleeping for {time_to_sleep} seconds\n\n")
    sleep(time_to_sleep)

# Main loop to go through all accounts
for index, phone in enumerate(config['accounts']):
    print(f"Attempting to send a message from phone: {phone}\n")
    test_message = test_messages[index % len(test_messages)]
    # Prefer telethon_sessions/{phone}.session if it exists
    telethon_session = os.path.join('telethon_sessions', f'{phone}.session')
    session_session = os.path.join(folder_session, phone)
    if os.path.exists(telethon_session):
        session_file = os.path.join('telethon_sessions', phone)
    else:
        session_file = session_session

    client = TelegramClient(session_file, config['api_id'], config['api_hash'])

    try:
        client.connect()
        if not client.is_user_authorized():
            print(f"User not authorized for {phone}. Skipping.")
            continue

        with client:
            try:
                # Try to resolve group entity for better error output
                group_entity = client.get_entity(group_url)
                group_name = getattr(group_entity, 'title', str(group_entity))
            except Exception:
                group_name = '(unknown)'
            try:
                client.loop.run_until_complete(send_message(client, group_url, test_message))
            except Exception as e:
                print(f"Error for {phone}: {e}. Group: {group_name} | Link: {group_url}. Skipping.")
                continue
            
    except Exception as e:
        print(f"Error for {phone}: {e}. Group: (unknown) | Link: {group_url}. Skipping.")
        continue
    finally:
        client.disconnect()
