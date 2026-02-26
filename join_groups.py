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

# Read configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r') as f:
    config = json.loads(f.read())

api_id = config['api_id']
api_hash = config['api_hash']
group_target = config['join_group']
accounts = config['accounts']

folder_session = 'telethon_sessions/'

async def join_group(client, group_url, phone):
    try:
        # Get account display name
        me = await client.get_me()
        display_name = me.first_name if me.first_name else "Unknown"
        
        # Check if the group link is private (has '+')
        if re.match(r'https://t\.me/\+(.*)', group_url):
            invite_code = group_url.split('+')[1]
            await client(ImportChatInviteRequest(invite_code))
        else:
            await client(JoinChannelRequest(group_url))
        
        # Log successful join to file
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} ({display_name}) joined {group_url}\n"
        
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)
        
        print(f"Joined group {group_url} successfully.")
        print(f"Logged: {log_entry.strip()}")
    except Exception as e:
        print(f"Could not join group {group_url}: {e}")
        # Log failed join
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} FAILED to join {group_url}: {e}\n"
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)

async def process_account(phone):
    client = TelegramClient(folder_session + phone, api_id, api_hash)
    try:
        await client.start(phone)
        if await client.is_user_authorized():
            print(f"Processing with account {phone}")
            await join_group(client, group_target, phone)
        else:
            print(f"Authorization failed for account {phone}")
    except AuthKeyDuplicatedError:
        print(f"AuthKeyDuplicatedError for {phone}. Deleting session and re-logging in.")
        session_path = folder_session + phone + ".session"
        if os.path.exists(session_path):
            os.remove(session_path)
            print(f"Deleted session file: {session_path}")
        # Re-login
        client = TelegramClient(folder_session + phone, api_id, api_hash)
        await client.start(phone)  # This will prompt for code
        if await client.is_user_authorized():
            print(f"Re-logged in with account {phone}")
            await join_group(client, group_target, phone)
        else:
            print(f"Authorization failed for account {phone} after re-login")
    except (SessionPasswordNeededError, PhoneNumberInvalidError) as e:
        print(f"Login error for {phone}: {e}")
    except sqlite3.OperationalError as e:
        print(f"[ERROR] sqlite3.OperationalError for account {phone}: {e}. Skipping to next account.")
        # Log the error
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} SQLITE ERROR: {e}\n"
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Unexpected error for account {phone}: {e}")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Account {phone} UNEXPECTED ERROR: {e}\n"
        with open('join_log.txt', 'a') as f:
            f.write(log_entry)
    finally:
        try:
            await client.disconnect()
        except sqlite3.OperationalError as e:
            print(f"[ERROR] sqlite3.OperationalError during disconnect for account {phone}: {e}. Skipping.")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - Account {phone} SQLITE ERROR DURING DISCONNECT: {e}\n"
            with open('join_log.txt', 'a') as f:
                f.write(log_entry)

async def main():
    for phone in accounts:
        await process_account(phone)
        random_sleep = random.uniform(1, 2)
        time.sleep(random_sleep)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
