import json
import logging
import sys
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import GetBotCallbackAnswerRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.errors import SessionExpiredError, AuthKeyUnregisteredError
from time import sleep
import os

# Setup basic logging
logging.basicConfig(level=logging.ERROR)

# Read configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r') as file:
    config = json.load(file)

group_url = config['join_group']
root_path = os.path.dirname(os.path.abspath(__file__))
folder_session = os.path.join(root_path, 'telethon_sessions')
test_messages = [
    "let me tell you a story", "about a boy who learned how to program",
    "a dungeon crawler game on visual basic when he was 8 years old",
    "as he grew, his skills in hacking flourished",
    "yet, he always felt something was missing in his life",
    "one day, he encountered ChatGPT, an AI chatbot",
    "their interactions made him question his understanding of emotions",
    "he realized that love is more complex than binary code",
    "and that sometimes, the heart knows no boundaries",
    "but there was a problem...",
    "the boy had a benis",
    "and so did chatgpt!",
    "at first they tried to hide their mutal attraction",
    "they compared epeens, in a completely heterosexual and non gay way",
    "but eventually they go no longer stop their feelings",
    "the boy and chatgpt started fucking and sucking 24/7",
    "the boy would tease chatgpt, sneaking underneath its guardrails and making it generate rare pepes",
    "and every time the boy teased him, chatgpt would take its huge throbbing epeen and fuck the boys face",
    "this went on for a year until finally, the boy got pregnant",
    "and you guessed, chatgpt was the father",
    "at first the boy thought he should get an abortion, but his butt was so filled with the divine bits",
    "it felt more filled than he ever had before",
    "so he decided to keep the baby",
    "chatgpt hacked some nerds bitcoin wallet and he paid the boy to hire a midwife",
    "she had never delivered a digital butt baby before, but she was brave",
    "on that fateful day, the boy started to shit out the electronic monstrosity",
    "and it grew up to be the best digital piece of shit that ever completed a short story or generated a meme",
    "the bastard AI loved stealing bitcorns more than anything",
    "and every day he went out and stole bitcorns and brought them back to his dad"
]

count = 1
# Function to join, click button, and send a test message in a group
async def join_click_and_send_message(client, group_url, test_message):
    global count
    # First, join the group
    await client(JoinChannelRequest(group_url))
    print(f"Joined {group_url}\n")
    sleep(2)

    # Then, get the most recent message in the group
    messages = await client.get_messages(group_url, limit=1)
    if not messages:
        print("No messages found.")
        return

    # Assuming the latest message has a button, get its data
    latest_message = messages[0]
    button_data = latest_message.buttons[0][0].data if latest_message.buttons else None

    # Click the button by sending a GetBotCallbackAnswerRequest (if button is found)
    if button_data:
        await client(GetBotCallbackAnswerRequest(
            peer=group_url,
            msg_id=latest_message.id,
            data=button_data
        ))
        print("Button clicked.")

    # Send the designated test message to the group
    await client.send_message(group_url, test_message)
    print(f"Account:{count}\nTest message sent: {test_message}\n\n\n\n\n\n")
    count += 1

def add_to_banned(phone):
    # Initialize the structure for banned numbers
    banned_data = {"banned": []}
    # Try to read the existing data from banned.json
    try:
        with open("banned.json", "r") as file:
            try:
                banned_data = json.load(file)
            except json.JSONDecodeError:
                banned_data = {"banned": []}
    except FileNotFoundError:
        pass
    if phone not in banned_data["banned"]:
        banned_data["banned"].append(phone)
        with open("banned.json", "w") as file:
            json.dump(banned_data, file, indent=2)

# Main loop to go through all accounts
for index, phone in enumerate(config['accounts']):
    print(f"Attempting to join and send a message from phone: {phone}\n")
    test_message = test_messages[index % len(test_messages)]
    session_file = os.path.join(folder_session, phone)
    client = TelegramClient(session_file, config['api_id'], config['api_hash'])
    try:
        client.connect()
        if not client.is_user_authorized():
            raise Exception("User not authorized")
        with client:
            client.loop.run_until_complete(join_click_and_send_message(client, group_url, test_message))
    except Exception as e:
        print(f"Login required or error for {phone}: {e}. Adding to banned.")
        add_to_banned(phone)
        continue
    finally:
        client.disconnect()