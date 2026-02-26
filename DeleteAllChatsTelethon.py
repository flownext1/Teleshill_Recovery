from telethon.sync import TelegramClient
import json
import os
import sys

# Read configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r') as f:
    config = json.load(f)

api_id = config['api_id']
api_hash = config['api_hash']
accounts = config['accounts']
session_dir = 'telethon_sessions'

for phone_number in accounts:
    print(f"\nProcessing account {phone_number}")
    client = TelegramClient(os.path.join(session_dir, phone_number), api_id, api_hash)
    client.connect()
    if not client.is_user_authorized():
        client.send_code_request(phone_number)
        try:
            client.sign_in(phone_number, input('Enter the code: '))
        except Exception as e:
            print(f"Login failed for {phone_number}: {e}")
            client.disconnect()
            continue

    # Get all dialogs and delete them using the simpler delete_dialog method
    dialogs = client.get_dialogs()
    print(f"Found {len(dialogs)} dialogs to delete")
    
    for dialog in dialogs:
        try:
            chat_title = getattr(dialog.entity, 'title', getattr(dialog.entity, 'first_name', str(dialog.entity.id)))
            print(f"Deleting dialog: {chat_title}")
            client.delete_dialog(dialog.entity)
            print(f"Successfully deleted: {chat_title}")
        except Exception as e:
            print(f"Failed to delete {chat_title}: {e}")

    client.disconnect()
    print(f"Finished processing account {phone_number}")