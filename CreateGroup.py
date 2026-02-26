import json
import os
import sys
from telethon.sync import TelegramClient
from telethon import functions, types
from time import sleep
from telethon.errors.rpcerrorlist import FloodWaitError
import random
from telethon.errors.rpcerrorlist import UsernameOccupiedError


# Define the function for setting the group photo
def set_group_photo(client, group_entity, image_path):
    try:
        # Upload and set the profile picture for the supergroup
        file = client.upload_file(image_path)
        client(functions.channels.EditPhotoRequest(
            channel=group_entity,
            photo=types.InputChatUploadedPhoto(file=file)
        ))
        print("Profile picture set successfully.")

        #this log out/ log in won't work until we feed it different api key/hash
    except FloodWaitError as e:
        print(f"Error setting profile picture: {e}")
        sleep(3)
        print("Logging out and trying again in a new session...")
        client.disconnect()
        
        # Create and use a new client session
        with TelegramClient('new_session_name', api_id, api_hash) as new_client:
            new_client.start()
            file = new_client.upload_file(image_path)
            new_client(functions.channels.EditPhotoRequest(
                channel=group_entity,
                photo=types.InputChatUploadedPhoto(file=file)
            ))
            print("Profile picture set successfully in new session.")

# Load configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file) as config_file_obj:
    config = json.load(config_file_obj)

    api_id = config["api_id"]
    api_hash = config["api_hash"]
    safeguard_bot_username = config["safeguard_bot_username"]
    token_name = config.get("new_group_title", config.get("token_name", ""))
    tagline = config.get("tagline", "")
    image_path = config.get("image_path", "profiles/profile.png")
    if not os.path.exists(image_path):
        print(f"[WARN] Image file not found: {image_path}, skipping profile picture...")
        image_path = None
    public_link = config.get("new_group_title", config.get("token_name", "")).replace(" ", "")
    welcome = f"{{mention}}! You made it. Welcome to the home of {token_name}: {tagline}"
    group_title = token_name
    group_about = config.get("new_group_about", f'Welcome to ${token_name}: {tagline}\n\nLinks:\n\nhttps://twitter.com/{token_name}')

accounts = config["accounts"]
folder_session = 'telethon_sessions/'
first_account = config.get("selected_account", accounts[0])

print(f"Using account: {first_account} from config file: {config_file}")
print(f"Creating group with title: {group_title}")
print(f"Group about: {group_about}")

with TelegramClient(f"{folder_session}/{first_account}", api_id, api_hash) as client:
    print(f"Connected to Telegram with account: {first_account}")
    
    # Create the public supergroup
    print("Creating public supergroup...")
    public_group = client(functions.channels.CreateChannelRequest(
        title=group_title,
        about=group_about,
        megagroup=True
    )).chats[0]
    print(f"Group created successfully! Group ID: {public_group.id}")
    print(f"Group title: {public_group.title}")
    print(f"Group username: {public_group.username}")
    
    public_group_entity = types.InputChannel(channel_id=public_group.id, access_hash=public_group.access_hash)
    print(f"Group entity created: {public_group_entity}")

    # Set a public link for the supergroup with retry logic
    base_public_link = public_link
    print(f"Attempting to set public link: {base_public_link}")
    while True:
        try:
            client(functions.channels.UpdateUsernameRequest(
                channel=public_group_entity,
                username=public_link
            ))
            print(f"Successfully set public link to: {public_link}")
            break
        except UsernameOccupiedError:
            digit = str(random.randint(1, 9))
            public_link = base_public_link + digit
            print(f"Username {public_link} is already taken, trying {public_link}...")

    # Call the function to set group photo (if image exists)
    if image_path and os.path.exists(image_path):
        print("Setting group profile picture...")
        set_group_photo(client, public_group_entity, image_path)
        print("Profile picture set successfully!")
    else:
        print("[SKIP] No profile picture set.")

    # Additional logic for adding Safeguard bot, setting up admin rights, etc., can be similar to your previous script
    # Define admin rights for the Safeguard bot
    print("Setting up Safeguard bot as admin...")
    admin_rights = types.ChatAdminRights(
        change_info=True,
        post_messages=True,
        edit_messages=True,
        delete_messages=True,
        ban_users=True,
        invite_users=True,
        pin_messages=True,
        add_admins=True,
        manage_call=True,
        anonymous=False,
        other=False
    )

    # Invite the Safeguard bot and promote it as admin in the private supergroup
    safeguard_bot = client.get_input_entity(safeguard_bot_username)
    client(functions.channels.InviteToChannelRequest(
        channel=public_group_entity,
        users=[safeguard_bot]
    ))
    client(functions.channels.EditAdminRequest(
        channel=public_group_entity,
        user_id=safeguard_bot,
        admin_rights=admin_rights,
        rank='bot'
    ))
    print("Safeguard bot added as admin successfully!")

    print(f"Public group '{group_title}' created and profile picture set. Sleeping for 3 seconds before sending the Rose setup messages.\n\n")

    sleep(3)
    setup_message = "/cleanservice on"
    print(f"Sending: {setup_message}")
    client.send_message(public_group_entity, setup_message)
    print("/cleanservice on sent\n\n")

    sleep(3)
    setup_message = "/goodbye off"
    print(f"Sending: {setup_message}")
    client.send_message(public_group_entity, setup_message)
    print("/goodbye off sent\n\n")
    sleep(3)

    setup_message = "/cleanwelcome on"
    print(f"Sending: {setup_message}")
    client.send_message(public_group_entity, setup_message)
    print("/cleanwelcome on sent\n\n")
    sleep(3)

    setup_message = f"/setwelcome {welcome}"
    print(f"Sending: {setup_message}")
    client.send_message(public_group_entity, setup_message)
    print("/setwelcome sent\n\n")
    sleep(3)
    

    #right now the correct message to reply to is message 8 which we know because we copied the message link
    #every time I add a command to the command set, we need to increment this by 2 (1 for the command and 1 for Roses response)
    print("Getting messages to find the correct one to reply to...")
    messages = client.get_messages(public_group_entity, limit=10)
    first_message = messages[8]  # Assuming the first message is the one you want to reply to
    print(f"Found message to reply to: {first_message.id}")
    

    # Reply to the first message
    reply_message = "/purge"
    print(f"Sending: {reply_message}")
    client.send_message(public_group_entity, reply_message, reply_to=first_message.id)
    print("Purged the chat\n\n")
    
    print(f"Group creation and setup completed successfully!")
    print(f"Group: {public_group.title}")
    print(f"Group ID: {public_group.id}")
    print(f"Public link: t.me/{public_link}")