from telethon import TelegramClient, types, utils  # Add 'types' to the import
import asyncio
import json
import random
import os
import sqlite3
from time import sleep
from itertools import cycle
import re
from telethon import functions

# Load the configuration
import os
config_file = os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

speed = 1
api_id = config['api_id']
api_hash = config['api_hash']
accounts = config['accounts']
target_group = config['group_target']
bot_commands = config['bot_commands']
token_name = config['token_name']

folder_session = 'session/'  # Directory for storing session files

def get_valid_session_path(phone):
    """Get valid session path, trying both session/ and telethon/ directories"""
    session_path = folder_session + phone
    if os.path.exists(session_path + ".session"):
        return session_path
    telethon_path = f"telethon/{phone}"
    if os.path.exists(telethon_path + ".session"):
        return telethon_path
    return None

# Function to get paths of all images in the memes folder
def get_image_paths(folder='memes'):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.png')]

# Function to get paths of all GIFs in the GIFS folder
def get_gif_paths(folder='GIFS'):
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.mp4')]

image_paths = get_image_paths()  # Load all image paths
gif_paths = get_gif_paths()     # Load all GIF paths

random.shuffle(image_paths)  # Shuffle the list of images
random.shuffle(gif_paths)    # Shuffle the list of GIFs

image_iter = iter(image_paths)  # Create an iterator for the list of images
gif_iter = iter(gif_paths)      # Create an iterator for the list of GIFs

async def send_command_with_account(client, command, target_entity):
    global image_iter, gif_iter

    if command == 'image' and image_paths:
        try:
            image_path = next(image_iter)
        except StopIteration:
            random.shuffle(image_paths)
            image_iter = iter(image_paths)
            image_path = next(image_iter)
        await client.send_file(target_entity, image_path)
        print(f"Image sent to {target_group}: {image_path}")

    elif command == 'gif' and gif_paths:
        try:
            gif_path = next(gif_iter)
        except StopIteration:
            random.shuffle(gif_paths)
            gif_iter = iter(gif_paths)
            gif_path = next(gif_iter)
        await client.send_file(target_entity, gif_path)
        print(f"GIF sent to {target_group}: {os.path.basename(gif_path)}")

    else:
        if command == "ca" or command == "contract":
            # Send the "ca" or "contract" command only once
            await client.send_message(target_entity, command)
            print(f"Command sent to {target_group}: {command}")
        else:
            times_to_send = random.randint(2, 15)
            for _ in range(times_to_send):
                await client.send_message(target_entity, command)
                print(f"Command sent to {target_group}: {command}")
                sleep(0.25)

async def main():
    while True:
        selected_accounts = random.sample(accounts, random.randint(3, len(accounts)))
        print(f"\n\nwe are using {len(selected_accounts)} accounts this pass\n\n")
        for phone in selected_accounts:
            commands_with_images_gifs = bot_commands + ['image'] * 6 + ['gif'] * 35
            command = random.choice(commands_with_images_gifs)

            # Get valid session path
            session_path = get_valid_session_path(phone)
            if not session_path:
                print(f"[ERROR] No valid session found for {phone}, skipping...")
                continue

            tried_telethon = False
            while True:
                try:
                    print(f"[INFO] Trying session: {session_path}")
                    client = TelegramClient(session_path, api_id, api_hash)
                    await client.start(phone)
                    
                    if not await client.is_user_authorized():
                        print(f"[ERROR] Account {phone} is not authorized in session {session_path}. Skipping.")
                        await client.disconnect()
                        break
                    
                    print(f"Client Created for {phone}")
                    target_entity = await client.get_entity(target_group)
                    await send_command_with_account(client, command, target_entity)
                    await client.disconnect()
                    break  # Success, exit loop
                    
                except sqlite3.OperationalError as e:
                    if not tried_telethon and os.path.exists(f"telethon/{phone}.session"):
                        print(f"[WARN] Session error for {phone} at {session_path}, trying telethon/{phone}.session instead.")
                        session_path = f"telethon/{phone}"
                        tried_telethon = True
                        continue
                    else:
                        print(f"[ERROR] Exception for account {phone}: {e}")
                        break
                except Exception as e:
                    print(f"[ERROR] Exception for account {phone}: {e}")
                    break

            sleep_time = random.randint(360,720)
            print(f"sleeping for {sleep_time} seconds")
            await asyncio.sleep(sleep_time)

asyncio.run(main())
