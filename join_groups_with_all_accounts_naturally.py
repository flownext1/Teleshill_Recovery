#!/usr/bin/env python3
import time
import random
import json
from time import sleep
import re
import os
import datetime
import sys
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors.rpcerrorlist import AuthKeyDuplicatedError
import sqlite3
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError

# Read configuration from command line argument or environment variable or default to testconfig.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'testconfig.json')
with open(config_file, 'r') as f:
    config = json.loads(f.read())

api_id = config['api_id']
api_hash = config['api_hash']
group_target = config['join_group']
accounts = config['accounts']

# Load names from names.json
try:
    with open('names.json', 'r') as f:
        names_config = json.loads(f.read())
        names = names_config.get('names', [])
except:
    names = []

folder_session = 'telethon_sessions/'

def get_name_for_phone(phone):
    """Get the display name for a phone number from names.json"""
    try:
        idx = accounts.index(phone)
        return names[idx] if idx < len(names) else phone
    except:
        return phone

async def join_group(client, group_link, phone):
    try:
        # Get account display name
        me = await client.get_me()
        display_name = me.first_name if me.first_name else "Unknown"
        
        # Check if the group link is private (has '+')
        if re.match(r'https://t\.me/\+(.*)', group_link):
            invite_code = group_link.split('+')[1]
            await client(ImportChatInviteRequest(invite_code))
        else:
            await client(JoinChannelRequest(group_link))
        
        # Log successful join to file
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} ({display_name}) joined {group_link}\n"
        
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)
        
        print(f"Joined group {group_link} successfully.")
        print(f"Logged: {log_entry.strip()}")
    except UserAlreadyParticipantError:
        print(f"Account {phone} is already a member of {group_link}.")
        # Log failed join
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} FAILED to join {group_link}: UserAlreadyParticipantError\n"
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error joining group {group_link} for account {phone}: {e}")
        # Log failed join
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} FAILED to join {group_link}: {e}\n"
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)

async def process_account(phone):
    print(f"[PROCESS] Starting processing for account: {phone}")
    session_path = folder_session + phone
    tried_telethon = False
    username = get_name_for_phone(phone)
    while True:
        try:
            client = TelegramClient(session_path, api_id, api_hash)
            
            async def custom_phone():
                print(f"[CODE REQUESTED] Enter code for {phone} ({username}): ")
                return input(f"[CODE REQUESTED] Enter code for {phone}: ")
            
            await client.start(phone=phone, code_callback=custom_phone)
            if await client.is_user_authorized():
                print(f"Processing with account {phone}")
                await join_group(client, group_target, phone)
            else:
                print(f"Authorization failed for account {phone}")
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

async def main():
    shuffled_accounts = accounts[:]  # Keep the original order
    for phone in shuffled_accounts:
        print(f"==========\n[INFO] About to process account: {phone}\n==========")
        try:
            await process_account(phone)
            print(f"[SUCCESS] Finished processing for account: {phone}")
        except Exception as e:
            print(f"[ERROR] Exception for account {phone}: {e}")
        # Sleep for a random time between 2 and 10 minutes (120-600 seconds)
        random_sleep = random.uniform(120, 600)
        print(f"Sleeping for {random_sleep:.1f} seconds before next join...")
        time.sleep(random_sleep)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main()) 