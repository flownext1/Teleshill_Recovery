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
import os
from time import sleep
import re
import sqlite3
from telethon.tl.functions.messages import ImportChatInviteRequest, SendReactionRequest
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
import telethon
from telethon.tl.types import ReactionEmoji
from datetime import datetime, timedelta, timezone
import sys
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

def main_menu():
    while True:
        print("\nMain Menu:")
        print("1. Account Management")
        print("2. Group Management")
        print("3. Messaging & Reactions")
        print("4. Group Cleanup & Moderation")
        print("5. Utilities & Tools")
        print("0. Exit")
        choice = input("Select a topic [0-5]: ").strip()
        if choice == '1':
            account_management_menu()
        elif choice == '2':
            group_management_menu()
        elif choice == '3':
            messaging_reactions_menu()
        elif choice == '4':
            group_cleanup_menu()
        elif choice == '5':
            utilities_menu()
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")
    sys.exit(0)

async def update_account_details(client, name, phone):
    try:
        display_name = name.replace("_", " ")
        await client(UpdateProfileRequest(first_name=display_name))
        print(f"Updated display name for account {phone} to {display_name}\n\n")

        username = name.replace("_", "")
        username = username.replace("(", "")
        username = username.replace(")", "")
        me = await client.get_me()
        current_username = me.username if hasattr(me, 'username') else None
        base_username = username
        while True:
            try:
                await client(UpdateUsernameRequest(username=username))
                print(f"Updated username for account {phone} to {username}\n\n")
                break
            except Exception as e:
                try:
                    me = await client.get_me()
                    current_username = me.username if hasattr(me, 'username') else None
                except Exception:
                    current_username = 'unknown (could not fetch)'
                print(f"Error updating account details for {phone}: {e}\nCurrent username: {current_username}\nTarget username: {username}\n\n")
                if 'FLOOD' in str(e).upper() or 'RATE LIMIT' in str(e).upper():
                    break
                digit = str(random.randint(1, 9))
                username = base_username + digit
                print(f"Trying new username: {username}\n\n")
    except Exception as e:
        try:
            me = await client.get_me()
            current_username = me.username if hasattr(me, 'username') else None
        except Exception:
            current_username = 'unknown (could not fetch)'
        print(f"Error updating account details for {phone}: {e}\nCurrent username: {current_username}\nTarget username: {username}\n\n")

async def change_profile_picture(client, phone, profile_index):
    try:
        profile_photos = await client.get_profile_photos('me')
        if profile_photos:
            await client(DeletePhotosRequest([InputPhoto(id=photo.id, access_hash=photo.access_hash, file_reference=photo.file_reference) for photo in profile_photos]))
            print(f"Deleted existing profile pictures for account {phone}\n\n")
        profile_picture_filename = f"profiles/profile{'' if profile_index == 0 else profile_index + 1}.png"
        await client(UploadProfilePhotoRequest(file=await client.upload_file(profile_picture_filename)))
        print(f"Uploaded new profile picture for account {phone} from {profile_picture_filename}\n\n")
    except Exception as e:
        print(f"Error changing profile picture for {phone}: {e}\n\n")

async def process_account(phone, name, profile_index):
    client = TelegramClient('telethon/' + phone, api_id, api_hash)
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

async def account_management_main():
    for index, (phone, name) in enumerate(zip(accounts, names)):
        await process_account(phone, name, index)
        random_sleep = random.uniform(5, 10)
        time.sleep(random_sleep)
        print(f"Sleeping for {random_sleep} seconds before moving on to the next account\n\n")

def account_management_menu():
    while True:
        print("\nAccount Management:")
        print("1. Change usernames, display names, and profile pictures")  # Option 1
        print("2. Add/remove accounts")  # Option 4
        print("3. Check for banned accounts in config.json (requires a target group)")  # Option 19
        print("4. Delete banned accounts from config.json (run 19 first)")  # Option 20
        print("0. Back")
        choice = input("Select an option: ").strip()
        if choice == '1':
            asyncio.run(account_management_main())
        elif choice == '2':
            modify_config_variables()
        elif choice == '3':
            command = ["gnome-terminal", "--", "bash", "-c", "python CheckSessionFiles_Join_SendMessage_.py; read -p '\nOk?\n'"]
            env = os.environ.copy()
            env['CONFIG_FILE'] = config_file
            subprocess.Popen(command, env=env)
        elif choice == '4':
            command = ["gnome-terminal", "--", "bash", "-c", "python DeleteBannedPhoneNumbers.py; read -p '\nOk?\n'"]
            subprocess.Popen(command)
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

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
                            elif "You have successfully requested to join this chat or channel" in msg:
                                failed += 1
                                account_failed_on_link[phone].add(link)
                                print(f"[PERM FAIL] {link} | {e}")
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

async def check_group_activity():
    links_file = "group_links_master.json"
    if not os.path.exists(links_file):
        print(f"No {links_file} found. Run option 25 first to build the master list.")
        return

    with open(links_file, 'r') as f:
        group_links = json.load(f)

    # Use the first available session for checking
    for phone in accounts:
        session_path = f"telethon/{phone}.session"
        if os.path.exists(session_path):
            api_id = config['api_id']
            api_hash = config['api_hash']
            break
    else:
        print("No valid /telethon session found for any account.")
        return

    active = []
    lukewarm = []
    dead = []

    async with TelegramClient(session_path, api_id, api_hash) as client:
        for link in group_links:
            try:
                entity = await client.get_entity(link)
                messages = await client.get_messages(entity, limit=1)
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
            except Exception as e:
                print(f"Could not access {link}: {e}")
                continue

    print(f"\n{GREEN}Active groups (last message today):{RESET}")
    for g in active:
        print(g)
    print(f"\n{YELLOW}Lukewarm groups (last message in one week):{RESET}")
    for g in lukewarm:
        print(g)
    print(f"\n{RED}Dead groups (last message over one week):{RESET}")
    for g in dead:
        print(g)

    leave_choice = input("\nDo you want to leave all dead groups and remove them from the master list? (y/n): ").strip().lower()
    if leave_choice == 'y':
        print(f"\nLeaving {len(dead)} dead groups...")
        async with TelegramClient(session_path, api_id, api_hash) as client:
            for link in dead:
                try:
                    entity = await client.get_entity(link)
                    await client(LeaveChannelRequest(entity))
                    print(f"Left group: {link}")
                except Exception as e:
                    print(f"Could not leave {link}: {e}")
        # Remove dead groups from the master list and save
        new_group_links = [g for g in group_links if g not in dead]
        with open(links_file, 'w') as f:
            json.dump(new_group_links, f, indent=2)
        print(f"Removed {len(dead)} dead groups from {links_file}.")
    else:
        print("No groups were left or removed.")

def group_management_menu():
    while True:
        print("\nGroup Management:")
        # print current target links from config first
        print(f"{CYAN}Current group_target: {config.get('group_target', 'Not set')}{RESET}")
        print(f"{CYAN}Current join_group: {config.get('join_group', 'Not set')}{RESET}\n")

        print("1. Join group with all accounts")  
        print("2. Join group with all accounts (natural/human-like)")  
        print("3. Leave target group")  
        print("4. Join all groups in master list with current config account")  
        print("5. Check if current accounts are members of target group")  
        print("6. Check group activity (Active/Lukewarm/Dead)")  
        print("7. Create group and set up Rose")  
        print("8. Create session and list group join links for a phone number")  
        print("0. Back")
        choice = input("Select an option: ").strip()
        env = os.environ.copy()
        env['CONFIG_FILE'] = 'config.json'  # Adjust as needed
        if choice == '1':
            command = ["gnome-terminal", "--", "bash", "-c", "python join_groups.py; read -p '\nOk?\n'"]
            subprocess.Popen(command, env=env)
        elif choice == '2':
            command = ["gnome-terminal", "--", "bash", "-c", "python join_groups_with_all_accounts_naturally.py; read -p '\nOk?\n'"]
            subprocess.Popen(command, env=env)
        elif choice == '3':
            command = ["gnome-terminal", "--", "bash", "-c", "python LeaveTargetGroup.py; read -p '\nOk?\n'"]
            subprocess.Popen(command)
        elif choice == '4':
            asyncio.run(join_all_groups_with_config_accounts(config, accounts))
        elif choice == '5':
            command = ["gnome-terminal", "--", "bash", "-c", "python check_membership.py; read -p '\nOk?\n'"]
            subprocess.Popen(command)
        elif choice == '6':
            asyncio.run(check_group_activity())
        elif choice == '7':
            command = ["gnome-terminal", "--", "bash", "-c", "python CreateGroup.py; read -p '\nOk?\n'"]
            subprocess.Popen(command, env=env)
        elif choice == '8':
            command = ["gnome-terminal", "--", "bash", "-c", "python Teleshill.py; read -p '\nOk?\n'"]
            subprocess.Popen(command, env=env)
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def messaging_reactions_menu():
    while True:
        print("\nMessaging & Reactions:")
        print("1. Start sending mass messages")  # Option 10
        print("2. Send Reactions")  # Option 12 (renamed)
        print("3. Remove reactions from most recent message in target group for all accounts")  # Option 23
        print("4. Send CA messages to degen groups")  # Option 21
        print("0. Back")
        choice = input("Select an option: ").strip()
        env = os.environ.copy()
        env['CONFIG_FILE'] = 'config.json'
        if choice == '1':
            command = ["gnome-terminal", "--", "bash", "-c", "python Send2.py; read -p '\nOk?\n'"]
            subprocess.Popen(command, env=env)
        elif choice == '2':
            command = ["gnome-terminal", "--", "bash", "-c", "python react.py; read -p '\nOk?\n'"]
            subprocess.Popen(command)
        elif choice == '3':
            import asyncio
            asyncio.run(react_remove_all_accounts())
        elif choice == '4':
            command = ["gnome-terminal", "--", "bash", "-c", "python SendHardcodedMessages.py; read -p '\nOk?\n'"]
            subprocess.Popen(command)
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def group_cleanup_menu():
    while True:
        print("\nGroup Cleanup & Moderation:")
        print("1. Delete chats for all accounts")  # Option 6
        print("2. Join and click to verify (doesnt work yet telethon cant click safeguard buttons)")  # Option 16
        print("0. Back")
        choice = input("Select an option: ").strip()
        env = os.environ.copy()
        env['CONFIG_FILE'] = 'config.json'  # Adjust as needed
        if choice == '1':
            command = ["gnome-terminal", "--", "bash", "-c", "python DeleteAllChatsTelethon.py; read -p '\nOk?\n'"]
            subprocess.Popen(command, env=env)
        elif choice == '2':
            command = ["gnome-terminal", "--", "bash", "-c", "python join_and_click.py; read -p '\nOk?\n'"]
            subprocess.Popen(command)
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

def utilities_menu():
    while True:
        print("\nUtilities & Tools:")
        print("1. Modify config variables (target group, etc.)")  # Option 24
        print("0. Back")
        choice = input("Select an option: ").strip()
        if choice == '1':
            modify_config_variables()
        elif choice == '0':
            break
        else:
            print("Invalid choice. Please try again.")

async def resolve_group(client, group):
    print(f"[RESOLVE_GROUP] Resolving group: {group} (type: {type(group)})")
    # If it's a t.me/joinchat or t.me/+ link, use ImportChatInviteRequest
    if group.startswith("https://t.me/+") or group.startswith("https://t.me/joinchat/"):
        invite_code = group.split("/")[-1].replace("+", "")
        print(f"[RESOLVE_GROUP] Using ImportChatInviteRequest with invite_code: {invite_code}")
        updates = await client(ImportChatInviteRequest(invite_code))
        entity = await client.get_entity(updates.chats[0].id)
        print(f"[RESOLVE_GROUP] Resolved entity from invite: {entity} (type: {type(entity)})")
        return entity
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
    telethon_path = f"telethon_sessions/{phone}"
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
        # Only sleep between accounts, not in a loop
        time.sleep(random.uniform(2, 5))
    # After all accounts have sent reactions, exit the function
    print(f"[DONE] Sent {x} reactions to the most recent message in the target group for each account.")


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
    print(f"\n{BOLD}{GREEN}=== CONFIG VARIABLE MODIFIER ==={RESET}")
    print(f"Current config file: {config_file}")
    print(f"Current target group: {config.get('group_target', 'Not set')}")
    with open(config_file, 'r') as f:
        current_config = json.load(f)
    print(f"\n{BOLD}Available variables to modify:{RESET}")
    print("1 - group_target")
    print("2 - join_group")
    print("3 - api_id")
    print("4 - api_hash")
    print("5 - Add new account")
    print("6 - Remove account")
    print("7 - View all current values")
    choice = input(f"\n{BLUE}Enter your choice [1-7]: {RESET}").strip()
    if choice == '1':
        new_group = input("Enter new group_target (t.me link or username): ").strip()
        current_config['group_target'] = new_group
        print(f"{GREEN}Updated group_target to: {new_group}{RESET}")
    elif choice == '2':
        new_join_group = input("Enter new join_group (t.me link or username): ").strip()
        current_config['join_group'] = new_join_group
        print(f"{GREEN}Updated join_group to: {new_join_group}{RESET}")
    elif choice == '3':
        new_api_id = input("Enter new api_id: ").strip()
        try:
            current_config['api_id'] = int(new_api_id)
            print(f"{GREEN}Updated api_id to: {new_api_id}{RESET}")
        except ValueError:
            print(f"{RED}Invalid api_id. Must be a number.{RESET}")
            return
    elif choice == '4':
        new_api_hash = input("Enter new api_hash: ").strip()
        current_config['api_hash'] = new_api_hash
        print(f"{GREEN}Updated api_hash to: {new_api_hash}{RESET}")
    elif choice == '5':
        new_account = input("Enter new phone number (with country code): ").strip()
        if new_account not in current_config['accounts']:
            current_config['accounts'].append(new_account)
            print(f"{GREEN}Added account: {new_account}{RESET}")
        else:
            print(f"{YELLOW}Account already exists in config.{RESET}")
    elif choice == '6':
        print(f"Current accounts: {current_config['accounts']}")
        account_to_remove = input("Enter phone number to remove: ").strip()
        if account_to_remove in current_config['accounts']:
            current_config['accounts'].remove(account_to_remove)
            print(f"{GREEN}Removed account: {account_to_remove}{RESET}")
        else:
            print(f"{RED}Account not found in config.{RESET}")
    elif choice == '7':
        print(f"\n{BOLD}Current config values:{RESET}")
        for key, value in current_config.items():
            if key == 'accounts':
                print(f"accounts: {len(value)} accounts")
                for i, account in enumerate(value, 1):
                    print(f"  {i}. {account}")
            else:
                print(f"{key}: {value}")
        return
    else:
        print(f"{RED}Invalid choice.{RESET}")
        return
    try:
        with open(config_file, 'w') as f:
            json.dump(current_config, f, indent=2)
        print(f"{GREEN}Config saved successfully to {config_file}{RESET}")
        print(f"{YELLOW}Note: Changes will take effect on next restart of Teleshill2.py{RESET}")
    except Exception as e:
        print(f"{RED}Error saving config: {e}{RESET}")


while True:

    print(title)
    print(f"{BOLD}{YELLOW}--- DEBUG MODE ENABLED ---{RESET}")
    print(f"Config file: {config_file}")
    print(f"Session folder: {folder_session}")
    print(f"Profile images directory: {profiles_directory}")
    print(f"Accounts ({len(accounts)}):")
    for i, phone in enumerate(accounts):
        username = names[i] if i < len(names) else '(no username)'
        session_path = folder_session + phone + ".session"
        print(f"  {i+1}. Phone: {phone} | Username: {username} | Session: {session_path}")
    print(f"--------------------------{RESET}\n")
    main_menu()
