#!/usr/bin/env python3
import asyncio
import time
import random
import json
from telethon.sync import TelegramClient
from telethon.tl.functions.photos import DeletePhotosRequest, UploadProfilePhotoRequest
from telethon.tl.functions.account import UpdateProfileRequest, UpdateUsernameRequest
from telethon.tl.types import InputPhoto
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError
import subprocess
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError, UsernameOccupiedError
from time import sleep
import re
import os
from telethon.tl.functions.messages import SendReactionRequest
import sqlite3
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.functions.channels import JoinChannelRequest
import telethon
from telethon.tl.types import ReactionEmoji
print(f"[DEBUG] Telethon version: {telethon.__version__}")
# Add terminal control screen
# ANSI escape codes for colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[2535m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Read configuration
with open('names.json', 'r') as f:
    config_names = json.loads(f.read())
# Add debug mode prompt at the very start
while True:
    debug_input = input('Enable debug mode? [y/n]: ').strip().lower()
    if debug_input in ['y', 'n']:
        DEBUG_MODE = debug_input == 'y'
        break
    else:
        print('Invalid input. Please enter y or n.')
# Prompt for environment
while True:
    env_choice = input('Select environment: [1] Testing, [2] Production, [3] Full: ').strip()
    if env_choice == '1':
        config_file = 'testconfig.json'
        break
    elif env_choice == '2':
        config_file = 'config.json'
        break
    elif env_choice == '3':
        config_file = 'fullconfig.json'
        break
    else:
        print('Invalid choice. Please enter 1 for Testing, 2 for Production, or 3 for Full.')

# Read configuration
with open(config_file, 'r') as f:
    config = json.loads(f.read())

api_id = config['api_id']
api_hash = config['api_hash']
accounts = config['accounts']
names = config_names['names']

folder_session = 'session/'
profiles_directory = 'profiles/'  # Directory where profile images are stored

# Debug output after environment selection
if 'DEBUG_MODE' in globals() and DEBUG_MODE:
    print(f"\n{BOLD}{YELLOW}--- DEBUG MODE ENABLED ---{RESET}")
    print(f"Config file: {config_file}")
    print(f"Session folder: {folder_session}")
    print(f"Profile images directory: {profiles_directory}")
    print(f"Accounts ({len(accounts)}):")
    for i, phone in enumerate(accounts):
        username = names[i] if i < len(names) else '(no username)'
        session_path = folder_session + phone + ".session"
        print(f"  {i+1}. Phone: {phone} | Username: {username} | Session: {session_path}")
    print(f"--------------------------{RESET}\n")




# ASCII Art Title
title = f"""{GREEN}

    ████████╗███████╗██╗░░░░░███████╗░██████╗██╗░░██╗██╗██╗░░░░░██╗░░░░░
    ╚══██╔══╝██╔════╝██║░░░░░██╔════╝██╔════╝██║░░██║██║██║░░░░░██║░░░░░
    ░░░██║░░░█████╗░░██║░░░░░█████╗░░╚█████╗░███████║██║██║░░░░░██║░░░░░
    ░░░██║░░░██╔══╝░░██║░░░░░██╔══╝░░░╚═══██╗██╔══██║██║██║░░░░░██║░░░░░
    ░░░██║░░░███████╗███████╗███████╗██████╔╝██║░░██║██║███████╗███████╗
    ░░░╚═╝░░░╚══════╝╚══════╝╚══════╝╚═════╝░╚═╝░░╚═╝╚═╝╚══════╝╚══════╝{RESET}
"""

# Fancy Menu System
menu = f"""{CYAN}
{BOLD}                      Command And Control Center{RESET}
                               version 1.1{RESET}
                               by syphermil{RESET}

----------------------------------------
1 - {GREEN}Change only usernames{RESET}
2 - {YELLOW}Change only display names{RESET}
3 - {BLUE}Change only profile pictures{RESET}
4 - {RED}Change usernames, display names, and profile pictures{RESET}
5 - {MAGENTA}Join group with all accounts{RESET}
5b - {MAGENTA}Join group with all accounts (natural/human-like){RESET}
6 - {CYAN}Delete chats for all accounts{RESET}
7 - {GREEN}Create group and set up Rose{RESET}
8 - {BLUE}Check if current accounts are members of target group{RESET}
9 - {YELLOW}Generate 100 new usernames{RESET}
10 - {GREEN}Start sending mass messages{RESET}
11 - {RED}Start sending dev messages{RESET}
12 - {BLUE}Send $X number of reactions to the most recent message in target group{RESET}
13 - {CYAN}Send mass messages 2x speed{RESET}
14 - {CYAN}Send mass messages 2x + dev messages{RESET}
15 - {CYAN}Send mass messages 2x + dev messages + copypasta & text{RESET}
16 - {RED}Join and click to verify{RESET}
17 - {GREEN}Leave Target Group{RESET}
18 - {YELLOW}React to most recent message X number of times{RESET}
19 - {CYAN}Check for banned accounts in config.json (requires a target group) {RESET}
20 - {RED}Delete banned accounts from config.json (run 19 first){RESET}
21 - {BLUE}Send CA messages to degen groups{RESET}
22 - {RED}React ❤ to most recent message in target group for all accounts{RESET}
23 - {BLUE}Remove reactions from most recent message in target group for all accounts{RESET}
24 - {GREEN}Modify config variables (target group, etc.){RESET}
25 - {GREEN}Create session and list group join links for a phone number{RESET}
26 - {GREEN}Join all groups in master list with current config account{RESET}
27 - {CYAN}Check group activity (Active/Lukewarm/Dead){RESET}
----------------------------------------
{BLUE}Enter your choice [1-27]: {RESET}"""


async def resolve_group(client, group):
    print(f"[RESOLVE_GROUP] Resolving group: {group} (type: {type(group)})")
    # If it's a t.me/joinchat or t.me/+ link, use ImportChatInviteRequest
    if group.startswith("https://t.me/+") or group.startswith("https://t.me/joinchat/"):
        invite_code = group.split("/")[-1].replace("+", "")
        print(f"[RESOLVE_GROUP] Using ImportChatInviteRequest with invite_code: {invite_code}")
        try:
            updates = await client(ImportChatInviteRequest(invite_code))
            entity = await client.get_entity(updates.chats[0].id)
            print(f"[RESOLVE_GROUP] Resolved entity from invite: {entity} (type: {type(entity)})")
            return entity
        except Exception as e:
            error_str = str(e).lower()
            print(f"[RESOLVE_GROUP] ImportChatInviteRequest failed: {e}")
            # If already a participant, get entity by iterating dialogs
            if "already a participant" in error_str or "already joined" in error_str:
                print(f"[RESOLVE_GROUP] Already a participant, searching dialogs...")
                
                # Iterate ALL dialogs and find the one with matching ID
                async for dialog in client.iter_dialogs():
                    entity = dialog.entity
                    if hasattr(entity, 'id'):
                        # Check if last digits match (supergroup format: -100XXXXXXXXXX)
                        id_str = str(entity.id)
                        # Remove -100 prefix for comparison
                        clean_id = id_str.replace('-100', '')
                        if clean_id.endswith(invite_code[-6:]) or id_str.endswith(invite_code[-6:]):
                            print(f"[RESOLVE_GROUP] Found matching dialog: {getattr(entity, 'title', 'unknown')} (id: {entity.id})")
                            # Verify we can use this entity
                            try:
                                verified = await client.get_entity(entity.id)
                                print(f"[RESOLVE_GROUP] Verified entity: {verified}")
                                return verified
                            except Exception as ve:
                                print(f"[RESOLVE_GROUP] Verify failed: {ve}")
                                continue
                
                # If still not found, try the specific ID we saw in logs (-1002562830359)
                print(f"[RESOLVE_GROUP] Trying known ID from logs...")
                try:
                    known_id = -1002562830359  # "not a kabal" group from logs
                    entity = await client.get_entity(known_id)
                    print(f"[RESOLVE_GROUP] Found entity with known ID: {entity}")
                    return entity
                except Exception as ke:
                    print(f"[RESOLVE_GROUP] Known ID also failed: {ke}")
                    
                raise Exception(f"Could not resolve group with invite code: {invite_code}")
            else:
                raise
    elif group.startswith("https://t.me/"):
        username = group.split("/")[-1]
        print(f"[RESOLVE_GROUP] Using get_entity with username: {username}")
        entity = await client.get_entity(username)
        print(f"[RESOLVE_GROUP] Resolved entity from username: {entity} (type: {type(entity)})")
        return entity
    else:
        print(f"[RESOLVE_GROUP] Using get_entity with group: {group}")
        entity = await client.get_entity(group)
        print(f"[RESOLVE_GROUP] Resolved entity from group: {entity} (type: {type(entity)})")
        return entity

async def react_heart_to_latest_message(client, target_group, phone):
    try:
        print(f"[HEART REACT] Resolving group for target_group: {target_group}")
        entity = await resolve_group(client, target_group)
        print(f"[HEART REACT] Got entity: {entity} (type: {type(entity)})")
        messages = await client.get_messages(entity, limit=1)
        print(f"[HEART REACT] Got messages: {messages} (type: {type(messages)})")
        if messages:
            latest_msg = messages[0]
            # Randomly choose between heart, rocketship, and thumbs up
            emoji_choices = ['❤', '🚀', '👍']
            chosen_emoji = random.choice(emoji_choices)
            print(f"[HEART REACT] Reacting to message ID: {latest_msg.id} with {chosen_emoji}")
            print(f"[HEART REACT] Reaction param: {[ReactionEmoji(emoticon=chosen_emoji)]} (type: {type([ReactionEmoji(emoticon=chosen_emoji)])})")
            await client(SendReactionRequest(
                peer=entity,
                msg_id=latest_msg.id,
                reaction=[ReactionEmoji(emoticon=chosen_emoji)]
            ))
            print(f"[HEART REACT] Account {phone} reacted {chosen_emoji} to message {latest_msg.id} in {target_group}")
        else:
            print(f"[HEART REACT] No messages found in {target_group} for account {phone}")
    except Exception as e:
        print(f"[HEART REACT ERROR] Account {phone}: {e}")

async def react_hearts_all_accounts():
    target_group = config.get('group_target')
    for phone in accounts:
        session_path = folder_session + phone
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
                try:
                    await react_heart_to_latest_message(client, target_group, phone)
                finally:
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
        time.sleep(random.uniform(2, 5))


# Find the function for option 18 and update its session logic:
import sqlite3
import os

def get_valid_session_path(phone):
    session_path = folder_session + phone
    if os.path.exists(session_path + ".session"):
        return session_path
    telethon_path = f"telethon/{phone}"
    if os.path.exists(telethon_path + ".session"):
        return telethon_path
    return None

async def react_x_times_to_latest_message(client, target_group, phone, x):
    try:
        print(f"[REACT X TIMES] Resolving group for target_group: {target_group}")
        entity = await resolve_group(client, target_group)
        print(f"[REACT X TIMES] Got entity: {entity} (type: {type(entity)})")
        messages = await client.get_messages(entity, limit=1)
        print(f"[REACT X TIMES] Got messages: {messages} (type: {type(messages)})")
        if messages:
            latest_msg = messages[0]
            print(f"[REACT X TIMES] Reacting to message ID: {latest_msg.id} {x} times")
            print(f"[REACT X TIMES] Reaction param: {[ReactionEmoji(emoticon='❤')]} (type: {type([ReactionEmoji(emoticon='❤')])})")
            for i in range(x):
                await client(SendReactionRequest(
                    peer=entity,
                    msg_id=latest_msg.id,
                    reaction=[ReactionEmoji(emoticon='❤')]
                ))
                print(f"[REACT X TIMES] Account {phone} reacted ❤ to message {latest_msg.id} (attempt {i+1}/{x})")
        else:
            print(f"[REACT X TIMES] No messages found in {target_group} for account {phone}")
    except Exception as e:
        print(f"[REACT X TIMES ERROR] Account {phone}: {e}")

async def react_x_times_all_accounts(x):
    target_group = config.get('group_target')
    for phone in accounts:
        session_path = folder_session + phone
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
                try:
                    # (your existing logic to react x times goes here)
                    # For example, call a function like react_x_times_to_latest_message(client, target_group, phone, x)
                    await react_x_times_to_latest_message(client, target_group, phone, x)
                finally:
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
        time.sleep(random.uniform(2, 5))


async def remove_reaction_from_latest_message(client, target_group, phone):
    try:
        print(f"[REMOVE REACT] Resolving group for target_group: {target_group}")
        entity = await resolve_group(client, target_group)
        print(f"[REMOVE REACT] Got entity: {entity} (type: {type(entity)})")
        messages = await client.get_messages(entity, limit=1)
        print(f"[REMOVE REACT] Got messages: {messages} (type: {type(messages)})")
        if messages:
            latest_msg = messages[0]
            print(f"[REMOVE REACT] Removing all reactions from message ID: {latest_msg.id}")
            await client(SendReactionRequest(
                peer=entity,
                msg_id=latest_msg.id,
                reaction=[]  # Remove all reactions from this account
            ))
            print(f"[REMOVE REACT] Account {phone} removed all reactions from message {latest_msg.id} in {target_group}")
        else:
            print(f"[REMOVE REACT] No messages found in {target_group} for account {phone}")
    except Exception as e:
        print(f"[REMOVE REACT ERROR] Account {phone}: {e}")

async def react_remove_all_accounts():
    target_group = config.get('group_target')
    for phone in accounts:
        session_path = folder_session + phone
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
                try:
                    await remove_reaction_from_latest_message(client, target_group, phone)
                finally:
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
        time.sleep(random.uniform(2, 5))

def modify_config_variables():
    """Function to modify config variables in the selected config file"""
    print(f"\n{BOLD}{GREEN}=== CONFIG VARIABLE MODIFIER ==={RESET}")
    print(f"Current config file: {config_file}")
    print(f"Current target group: {config.get('group_target', 'Not set')}")
    
    # Load current config
    with open(config_file, 'r') as f:
        current_config = json.load(f)
    
    # Check if group_target and join_group are in sync
    group_target = current_config.get('group_target')
    join_group = current_config.get('join_group')
    if group_target != join_group:
        print(f"{YELLOW}Warning: group_target and join_group are not in sync!{RESET}")
        print(f"group_target: {group_target}")
        print(f"join_group: {join_group}")
        sync_choice = input(f"{BLUE}Would you like to sync them? (y/n): {RESET}").strip().lower()
        if sync_choice == 'y':
            if group_target:
                current_config['join_group'] = group_target
                print(f"{GREEN}Synced join_group to group_target: {group_target}{RESET}")
            elif join_group:
                current_config['group_target'] = join_group
                print(f"{GREEN}Synced group_target to join_group: {join_group}{RESET}")
            else:
                print(f"{RED}Both values are empty. Please set one first.{RESET}")
                return
    
    print(f"\n{BOLD}Available variables to modify:{RESET}")
    print("1 - group (updates both group_target and join_group)")
    print("2 - api_id")
    print("3 - api_hash")
    print("4 - Add new account")
    print("5 - Remove account")
    print("6 - View all current values")
    
    choice = input(f"\n{BLUE}Enter your choice [1-6]: {RESET}").strip()
    
    if choice == '1':
        new_group = input("Enter new group (t.me link or username): ").strip()
        current_config['group_target'] = new_group
        current_config['join_group'] = new_group  # Keep them in sync
        print(f"{GREEN}Updated group_target and join_group to: {new_group}{RESET}")
        
    elif choice == '2':
        new_api_id = input("Enter new api_id: ").strip()
        try:
            current_config['api_id'] = int(new_api_id)
            print(f"{GREEN}Updated api_id to: {new_api_id}{RESET}")
        except ValueError:
            print(f"{RED}Invalid api_id. Must be a number.{RESET}")
            return
            
    elif choice == '3':
        new_api_hash = input("Enter new api_hash: ").strip()
        current_config['api_hash'] = new_api_hash
        print(f"{GREEN}Updated api_hash to: {new_api_hash}{RESET}")
        
    elif choice == '4':
        new_account = input("Enter new phone number (with country code): ").strip()
        if new_account not in current_config['accounts']:
            current_config['accounts'].append(new_account)
            print(f"{GREEN}Added account: {new_account}{RESET}")
        else:
            print(f"{YELLOW}Account already exists in config.{RESET}")
            
    elif choice == '5':
        print(f"Current accounts: {current_config['accounts']}")
        account_to_remove = input("Enter phone number to remove: ").strip()
        if account_to_remove in current_config['accounts']:
            current_config['accounts'].remove(account_to_remove)
            print(f"{GREEN}Removed account: {account_to_remove}{RESET}")
        else:
            print(f"{RED}Account not found in config.{RESET}")
            
    elif choice == '6':
        print(f"\n{BOLD}Current config values:{RESET}")
        for key, value in current_config.items():
            if key == 'accounts':
                print(f"accounts: {len(value)} accounts")
                for i, account in enumerate(value, 1):
                    print(f"  {i}. {account}")
            elif key in ['group_target', 'join_group']:
                print(f"{key}: {value} {'(SYNCED)' if current_config.get('group_target') == current_config.get('join_group') else '(NOT SYNCED)'}")
            else:
                print(f"{key}: {value}")
        return
        
    else:
        print(f"{RED}Invalid choice.{RESET}")
        return
    
    # Save updated config
    try:
        with open(config_file, 'w') as f:
            json.dump(current_config, f, indent=2)
        print(f"{GREEN}Config saved successfully to {config_file}{RESET}")
        print(f"{YELLOW}Note: Changes will take effect on next restart of Teleshill.py{RESET}")
        
    except Exception as e:
        print(f"{RED}Error saving config: {e}{RESET}")


while True:

    print(title)
    print(menu, end="")
    # Show target group in debug mode after menu
    if 'DEBUG_MODE' in globals() and DEBUG_MODE:
        group_target = config.get('group_target', None)
        if group_target:
            print(f"{BOLD}{YELLOW}Current target group: {group_target}{RESET}")
        else:
            print(f"{BOLD}{YELLOW}No target group set in config file.{RESET}")
    choice = input("")



















    async def update_account_details(client, name, phone):
        try:
            # Check if user chose to update display names or all
            if choice in ['2', '4']:
                display_name = name.replace("_", " ")
                await client(UpdateProfileRequest(first_name=display_name))
                print(f"Updated display name for account {phone} to {display_name}\n\n")

            # Check if user chose to update usernames or all
            if choice in ['1', '4']:
                username = name.replace("_", "")
                username = username.replace("(", "")
                username = username.replace(")", "")
                # Fetch current username
                me = await client.get_me()
                current_username = me.username if hasattr(me, 'username') else None
                import random
                base_username = username
                while True:
                    try:
                        await client(UpdateUsernameRequest(username=username))
                        print(f"Updated username for account {phone} to {username}\n\n")
                        break  # Username change was successful, exit the loop
                    except Exception as e:
                        # Always print error and attempted usernames
                        try:
                            me = await client.get_me()
                            current_username = me.username if hasattr(me, 'username') else None
                        except Exception:
                            current_username = 'unknown (could not fetch)'
                        print(f"Error updating account details for {phone}: {e}\nCurrent username: {current_username}\nTarget username: {username}\n\n")
                        # If it's a flood/rate limit error, break
                        if 'FLOOD' in str(e).upper() or 'RATE LIMIT' in str(e).upper():
                            break
                        # Otherwise, try a new random digit
                        digit = str(random.randint(1, 9))
                        username = base_username + digit
                        print(f"Trying new username: {username}\n\n")
        except Exception as e:
            # Print current and target username on error
            try:
                me = await client.get_me()
                current_username = me.username if hasattr(me, 'username') else None
            except Exception:
                current_username = 'unknown (could not fetch)'
            print(f"Error updating account details for {phone}: {e}\nCurrent username: {current_username}\nTarget username: {username}\n\n")

    async def change_profile_picture(client, phone, profile_index):
        try:
            # Check if user chose to update profile pictures or all
            if choice in ['3', '4']:
                profile_photos = await client.get_profile_photos('me')
                if profile_photos:
                    await client(DeletePhotosRequest([InputPhoto(id=photo.id, access_hash=photo.access_hash, file_reference=photo.file_reference) for photo in profile_photos]))
                    print(f"Deleted existing profile pictures for account {phone}\n\n")

                profile_picture_filename = f"{profiles_directory}profile{'' if profile_index == 0 else profile_index + 1}.png"
                await client(UploadProfilePhotoRequest(file=await client.upload_file(profile_picture_filename)))
                print(f"Uploaded new profile picture for account {phone} from {profile_picture_filename}\n\n")
        except Exception as e:
            print(f"Error changing profile picture for {phone}: {e}\n\n")

    async def process_account(phone, name, profile_index):
        client = TelegramClient(folder_session + phone, api_id, api_hash)
        await client.start(phone)
        
        try:
            if await client.is_user_authorized():
                print(f"Processing with account {phone}\n\n")
                await update_account_details(client, name, phone)
                await change_profile_picture(client, phone, profile_index)
            else:
                print(f"Authorization failed for account {phone}\n\n")
        except (SessionPasswordNeededError, PhoneNumberInvalidError) as e:
            print(f"Login error for {phone}: {e}\n\n")
        finally:
            await client.disconnect()

    async def main():
        for index, (phone, name) in enumerate(zip(accounts, names)):
            await process_account(phone, name, index)
            random_sleep = random.uniform(5, 10)
            time.sleep(random_sleep)
            print(f"Sleeping for {random_sleep} seconds before moving on to the next account\n\n")
    if choice == '5':
        command = ["gnome-terminal", "--", "bash", "-c", "python join_groups.py; read -p '\nOk?\n'"]
        env = os.environ.copy()
        env['CONFIG_FILE'] = config_file
        subprocess.Popen(command, env=env)
    elif choice == '5b':
        command = ["gnome-terminal", "--", "bash", "-c", "python join_groups_with_all_accounts_naturally.py; read -p '\nOk?\n'"]
        env = os.environ.copy()
        env['CONFIG_FILE'] = config_file
        subprocess.Popen(command, env=env)
    elif choice == '6':
        command = ["gnome-terminal", "--", "bash", "-c", "python DeleteAllChatsTelethon.py; read -p '\nOk?\n'"]
        env = os.environ.copy()
        env['CONFIG_FILE'] = config_file
        subprocess.Popen(command, env=env)
    elif choice == '7':
        command = ["gnome-terminal", "--", "bash", "-c", "python CreateGroup.py; read -p '\nOk?\n'"]
        env = os.environ.copy()
        env['CONFIG_FILE'] = config_file
        subprocess.Popen(command, env=env)
    elif choice == '8':
        command = ["gnome-terminal", "--", "bash", "-c", "python check_membership.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '9':
        command = ["gnome-terminal", "--", "bash", "-c", "python nameGen.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '10':
        # Use Send2.py instead of SendMessage.py, and pass CONFIG_FILE env var
        command = ["gnome-terminal", "--", "bash", "-c", "python Send2.py; read -p '\nOk?\n'"]
        env = os.environ.copy()
        env['CONFIG_FILE'] = config_file
        subprocess.Popen(command, env=env)
    elif choice == '11':
        command = ["gnome-terminal", "--", "bash", "-c", "python dev_message.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '12':
        command = ["gnome-terminal", "--", "bash", "-c", "python react.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '13':
        command = ["gnome-terminal", "--", "bash", "-c", "python SendMessage.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
        sleep(1)
        command = ["gnome-terminal", "--", "bash", "-c", "python SendMessage2x.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '14':
        command = ["gnome-terminal", "--", "bash", "-c", "python SendMessage.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
        sleep(1)
        command = ["gnome-terminal", "--", "bash", "-c", "python SendMessage2x.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
        sleep(1)
        command = ["gnome-terminal", "--", "bash", "-c", "python dev_message.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '15':
        command = ["gnome-terminal", "--", "bash", "-c", "python SendMessage.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
        sleep(1)
        command = ["gnome-terminal", "--", "bash", "-c", "python SendMessage2x.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
        sleep(1)
        command = ["gnome-terminal", "--", "bash", "-c", "python dev_message.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
        sleep(1)
        command = ["gnome-terminal", "--", "bash", "-c", "python sendCopypasta.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '16':
        command = ["gnome-terminal", "--", "bash", "-c", "python join_and_click.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '17':
        command = ["gnome-terminal", "--", "bash", "-c", "python LeaveTargetGroup.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '18':
        command = ["gnome-terminal", "--", "bash", "-c", "python react.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '19':
        command = ["gnome-terminal", "--", "bash", "-c", "python CheckSessionFiles_Join_SendMessage_.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '20':
        command = ["gnome-terminal", "--", "bash", "-c", "python DeleteBannedPhoneNumbers.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '21':
        command = ["gnome-terminal", "--", "bash", "-c", "python SendHardcodedMessages.py; read -p '\nOk?\n'"]
        subprocess.Popen(command)
    elif choice == '22':
        import asyncio
        asyncio.run(react_hearts_all_accounts())
    elif choice == '23':
        import asyncio
        asyncio.run(react_remove_all_accounts())
    elif choice == '24':
        modify_config_variables()
    elif choice == '25':
        import asyncio
        import json
        async def create_session_and_list_groups():
            phone = input("Enter phone number (with country code): ").strip()
            telethon_path = f"telethon/{phone}.session"
            links_file = "group_links_master.json"
            usernames_file = "group_usernames_master.json"
            # Load existing links if file exists
            if os.path.exists(links_file):
                with open(links_file, 'r') as f:
                    saved_links = set(json.load(f))
            else:
                saved_links = set()
            # Load existing usernames/userids if file exists
            if os.path.exists(usernames_file):
                with open(usernames_file, 'r') as f:
                    saved_usernames = set((entry['username'], entry['user_id']) for entry in json.load(f))
                    usernames_data = [dict(username=u, user_id=uid) for u, uid in saved_usernames]
            else:
                saved_usernames = set()
                usernames_data = []
            if os.path.exists(telethon_path):
                print(f"Session already exists for {phone} in /telethon.")
            else:
                print(f"No session found for {phone} in /telethon. Creating new session...")
                client = TelegramClient(f"telethon/{phone}", api_id, api_hash)
                await client.start(phone)
                await client.disconnect()
                print(f"Session created for {phone} in /telethon.")
            # Now connect and list groups
            client = TelegramClient(f"telethon/{phone}", api_id, api_hash)
            await client.start(phone)
            if not await client.is_user_authorized():
                print(f"Account {phone} is not authorized.")
                await client.disconnect()
                return
            print(f"Connected to {phone}. Fetching group list...")
            dialogs = await client.get_dialogs()
            found = False
            new_links = set()
            new_usernames = set()
            for dialog in dialogs:
                entity = dialog.entity
                if hasattr(entity, 'megagroup') and entity.megagroup:
                    try:
                        full = await client.get_entity(entity.id)
                        if hasattr(full, 'username') and full.username:
                            link = f"https://t.me/{full.username}"
                            if link in saved_links:
                                print(f"[DUPLICATE LINK] Group: {entity.title} | Link: {link}")
                            else:
                                print(f"[UNIQUE LINK] Group: {entity.title} | Link: {link}")
                                new_links.add(link)
                                found = True
                            uname_pair = (full.username, full.id)
                            if uname_pair in saved_usernames:
                                print(f"[DUPLICATE USERNAME] Username: {full.username} | UserID: {full.id}")
                            else:
                                print(f"[UNIQUE USERNAME] Username: {full.username} | UserID: {full.id}")
                                new_usernames.add(uname_pair)
                    except Exception as e:
                        continue
            if new_links:
                all_links = saved_links.union(new_links)
                with open(links_file, 'w') as f:
                    json.dump(sorted(list(all_links)), f, indent=2)
                print(f"Saved {len(new_links)} new group links to {links_file}.")
            else:
                print("No new groups with visible join links found.")
            if new_usernames:
                all_usernames = saved_usernames.union(new_usernames)
                usernames_data = [dict(username=u, user_id=uid) for u, uid in all_usernames]
                with open(usernames_file, 'w') as f:
                    json.dump(usernames_data, f, indent=2)
                print(f"Saved {len(new_usernames)} new usernames/userids to {usernames_file}.")
            else:
                print("No new usernames/userids found.")
            await client.disconnect()
        asyncio.run(create_session_and_list_groups())
    elif choice == '26':
        async def join_all_groups_with_config_accounts(config, accounts):
            links_file = "group_links_master.json"
            if not os.path.exists(links_file):
                print(f"No {links_file} found. Run option 25 first to build the master list.")
                return

            with open(links_file, 'r') as f:
                group_links = json.load(f)

            joined = 0
            failed = 0
            account_next_available = {phone: 0 for phone in accounts}
            account_failed_on_link = {phone: set() for phone in accounts}

            try:
                for link in group_links:
                    while True:
                        now = time.time()
                        available_accounts = [p for p in accounts if now >= account_next_available[p] and link not in account_failed_on_link[p]]

                        # If all accounts have failed for this link, move to next link
                        if all(link in account_failed_on_link[p] for p in accounts):
                            print(f"[ALL FAILED] All accounts failed for {link}, moving to next link.")
                            break

                        if not available_accounts:
                            soonest = min(account_next_available.values(), default=now + 1)
                            sleep_time = max(soonest - now, 1)
                            print(f"[WAIT] No available accounts for {link}, sleeping {sleep_time:.1f} seconds...")
                            await asyncio.sleep(sleep_time)
                            continue

                        joined_this_group = False

                        for phone in available_accounts:
                            session_path = f"telethon/{phone}.session"
                            if not os.path.exists(session_path):
                                print(f"[MISSING SESSION] No session for {phone}, skipping.")
                                continue

                            api_id = config['api_id']
                            api_hash = config['api_hash']
                            # Print phone and username before starting client (in case code prompt happens)
                            username = None
                            try:
                                idx = accounts.index(phone)
                                username = names[idx] if idx < len(names) else None
                            except Exception:
                                username = None
                            print(f"[LOGIN ATTEMPT] Phone: {phone} Username: {username if username else '(unknown)'}")
                            client = TelegramClient(session_path, api_id, api_hash)

                            try:
                                try:
                                    await client.start(phone)
                                except (sqlite3.OperationalError, Exception) as e:
                                    print(f"[START ERROR] {e} for {phone}, skipping.")
                                    await client.disconnect()
                                    continue

                                if not await client.is_user_authorized():
                                    print(f"[UNAUTHORIZED] {phone} is not authorized.")
                                    await client.disconnect()
                                    continue

                                try:
                                    await client(JoinChannelRequest(link))
                                    print(f"[JOINED] {link} via {phone}")
                                    joined += 1
                                    joined_this_group = True
                                    await client.disconnect()
                                    break

                                except Exception as e:
                                    msg = str(e)
                                    wait_match = re.search(r'A wait of (\d+) seconds is required', msg)

                                    if wait_match:
                                        wait_time = int(wait_match.group(1)) + 1
                                        account_next_available[phone] = time.time() + wait_time
                                        print(f"[RATE LIMIT] {phone} wait {wait_time}s -> {link}")
                                    else:
                                        failed += 1
                                        account_failed_on_link[phone].add(link)
                                        print(f"[FAILED] {link} | {e}")

                                    await client.disconnect()
                                    continue

                            except KeyboardInterrupt:
                                print(f"\n[INTERRUPT] Disconnecting {phone} cleanly...")
                                await client.disconnect()
                                raise

                        if joined_this_group:
                            break

                print(f"[DONE] Joined: {joined}, Failed: {failed}")

            except KeyboardInterrupt:
                print("\n[EXITING] Interrupted.")

        asyncio.run(join_all_groups_with_config_accounts(config, accounts))
    elif choice == '27':
        import json
        import os
        from datetime import datetime, timedelta, timezone
        from telethon.sync import TelegramClient
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.errors import UserAlreadyParticipantError
        print(f"\n{BOLD}{CYAN}=== Checking Group Activity (Active/Lukewarm/Dead) ==={RESET}")
        # Load group links
        links_file = "group_links_master.json"
        if not os.path.exists(links_file):
            print(f"{RED}No {links_file} found. Run option 25 first to build the master list.{RESET}")
        else:
            with open(links_file, 'r') as f:
                group_links = json.load(f)
            phone = accounts[0]
            session_path = f"telethon/{phone}"
            api_id = config['api_id']
            api_hash = config['api_hash']
            active = []
            lukewarm = []
            dead = []
            with TelegramClient(session_path, api_id, api_hash) as client:
                for link in group_links:
                    try:
                        entity = client.get_entity(link)
                    except Exception:
                        try:
                            client(JoinChannelRequest(link))
                            entity = client.get_entity(link)
                        except UserAlreadyParticipantError:
                            entity = client.get_entity(link)
                        except Exception as e:
                            print(f"Could not access {link}: {e}")
                            continue
                    messages = client.get_messages(entity, limit=1)
                    if not messages:
                        print(f"No messages found in {link}")
                        continue
                    last_msg = messages[0]
                    last_date = last_msg.date.astimezone(timezone.utc)
                    now = datetime.now(timezone.utc)
                    if last_date.date() == now.date():
                        active.append(link)
                    elif now - last_date <= timedelta(days=7):
                        lukewarm.append(link)
                    else:
                        dead.append(link)
            print(f"\n{GREEN}Active groups (last message today):{RESET}")
            for g in active:
                print(g)
            print(f"\n{YELLOW}Lukewarm groups (last message in one week):{RESET}")
            for g in lukewarm:
                print(g)
            print(f"\n{RED}Dead groups (last message over one week):{RESET}")
            for g in dead:
                print(g)
    elif choice == 'exit':
        break


async def send_dm_to_all_chats():
    print(f"\n{BOLD}{GREEN}=== SEND DM TO ALL CHATS ==={RESET}")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    daily_msg_dir = os.path.join(script_dir, "daily_message")
    msg_path = os.path.join(daily_msg_dir, "message.txt")
    msg_no_image_path = os.path.join(daily_msg_dir, "message_no_image.txt")
    image_path = os.path.join(daily_msg_dir, "meme.png")
    
    if not os.path.exists(msg_path):
        print(f"Error: {msg_path} not found!")
        return
    
    with open(msg_path, 'r') as f:
        message = f.read().strip()
    print(f"Loaded message from: {msg_path}")
    
    if os.path.exists(msg_no_image_path):
        with open(msg_no_image_path, 'r') as f:
            message_no_image = f.read().strip()
        print(f"Loaded fallback message: {msg_no_image_path}")
    else:
        message_no_image = message
        print("No message_no_image.txt found, will use same message.")
    
    if os.path.exists(image_path):
        print(f"Found image: {image_path}")
    else:
        image_path = None
        print("No meme.png found, will send text only.")
    
    print(f"\nAvailable accounts:")
    for i, acc in enumerate(accounts):
        print(f"  {i+1}. {acc}")
    print(f"  0. Use first account ({accounts[0]})")
    print(f"  a. Use ALL accounts")
    
    account_choice = input(f"Select account [0-{len(accounts)}] or 'a' for all: ").strip().lower()
    
    if account_choice == 'a':
        selected_accounts = accounts
        print(f"\nUsing ALL {len(accounts)} accounts")
    elif account_choice == '0' or account_choice == '':
        selected_accounts = [accounts[0]]
    else:
        try:
            idx = int(account_choice) - 1
            if 0 <= idx < len(accounts):
                selected_accounts = [accounts[idx]]
            else:
                selected_accounts = [accounts[0]]
        except:
            selected_accounts = [accounts[0]]
    
    confirm = input(f"Send to all chats with {len(selected_accounts)} account(s)? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    all_scanned_groups = []
    all_log_entries = []
    total_sent = 0
    total_failed = 0
    
    for phone in selected_accounts:
        session_path = folder_session + phone
        
        print(f"\n{'='*50}")
        print(f"[INFO] Starting with account: {phone}")
        print(f"{'='*50}")
        
        try:
            client = TelegramClient(session_path, api_id, api_hash)
            await client.start(phone)
            
            if not await client.is_user_authorized():
                print(f"[ERROR] Account {phone} is not authorized. Skipping.")
                all_log_entries.append(f"ACCOUNT {phone}: NOT AUTHORIZED")
                await client.disconnect()
                continue
            
            sent_count = 0
            failed_count = 0
            scanned_groups = []
            log_entries = []
            
            print("[INFO] Iterating through all chats...")
            
            try:
                async for dialog in client.iter_dialogs():
                    try:
                        entity = dialog.entity
                        chat_type = type(entity).__name__
                        chat_title = getattr(entity, 'title', '') or getattr(entity, 'username', 'unknown')
                        
                        if chat_type == 'Channel' and getattr(entity, 'broadcast', False):
                            continue
                        
                        if chat_type == 'Chat':
                            if getattr(entity, 'deactivated', False) or getattr(entity, 'left', False):
                                continue
                        
                        if chat_type == 'User':
                            if not getattr(entity, 'username', None):
                                continue
                        
                        scanned_groups.append(f"{chat_title} ({chat_type})")
                        
                        sent_msg = False
                        if image_path and os.path.exists(image_path):
                            try:
                                await client.send_file(entity, image_path, caption=message)
                                print(f"[SENT] Image+text to: {chat_title}")
                                log_entries.append(f"SUCCESS: {chat_title} ({chat_type}) - Image+text")
                                sent_msg = True
                            except Exception as img_err:
                                if "PHOTOS_FORBIDDEN" in str(img_err) or "SEND_MEDIA_FORBIDDEN" in str(img_err):
                                    try:
                                        await client.send_message(entity, message_no_image)
                                        print(f"[SENT] Text (no_image) to: {chat_title}")
                                        log_entries.append(f"SUCCESS: {chat_title} ({chat_type}) - Text (image blocked)")
                                        sent_msg = True
                                    except Exception as e:
                                        print(f"[FAILED] {chat_title}: {e}")
                                        log_entries.append(f"FAILED: {chat_title} - {str(e)}")
                        
                        if not sent_msg:
                            try:
                                await client.send_message(entity, message)
                                print(f"[SENT] Text to: {chat_title}")
                                log_entries.append(f"SUCCESS: {chat_title} ({chat_type}) - Text")
                                sent_msg = True
                            except Exception as e:
                                print(f"[FAILED] {chat_title}: {e}")
                                log_entries.append(f"FAILED: {chat_title} - {str(e)}")
                        
                        if sent_msg:
                            sent_count += 1
                        
                        await asyncio.sleep(random.uniform(2.0, 4.0))
                        
                    except Exception as e:
                        print(f"[ERROR] {str(e)}")
                        continue
            except Exception as e:
                print(f"[ERROR] During iteration: {str(e)}")
            
            await client.disconnect()
            
        except Exception as e:
            print(f"[ERROR] Failed with account {phone}: {str(e)}")
            log_entries.append(f"ACCOUNT {phone} ERROR: {str(e)}")
            try:
                await client.disconnect()
            except:
                pass
        
        all_scanned_groups.extend(scanned_groups)
        all_log_entries.extend(log_entries)
        total_sent += sent_count
        total_failed += failed_count
        
        all_log_entries.append("")
        all_log_entries.append(f"=== Account {phone} Summary ===")
        all_log_entries.append(f"Groups scanned: {len(scanned_groups)}, Sent: {sent_count}, Failed: {failed_count}")
    
    output_path = os.path.join(daily_msg_dir, "output.txt")
    with open(output_path, 'w') as f:
        f.write(f"DM CAMPAIGN RESULTS\n")
        f.write(f"=" * 50 + "\n")
        f.write(f"Accounts used: {len(selected_accounts)}\n")
        f.write(f"Total groups scanned: {len(all_scanned_groups)}\n")
        f.write(f"Total successfully sent: {total_sent}\n")
        f.write(f"Total failed: {total_failed}\n")
        f.write(f"\n" + "=" * 50 + "\n")
        f.write(f"ALL GROUPS SCANNED:\n")
        for g in all_scanned_groups:
            f.write(f"  - {g}\n")
        f.write(f"\n" + "=" * 50 + "\n")
        f.write(f"DETAILED RESULTS:\n")
        for entry in all_log_entries:
            f.write(f"{entry}\n")
    
    print(f"\n[DONE] Total: {total_sent} sent, {total_failed} failed across {len(selected_accounts)} account(s)")
    print(f"Log saved to: {output_path}")


if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
