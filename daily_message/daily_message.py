#!/usr/bin/env python3
import asyncio
import os
import json
import time
import random
import sqlite3
from telethon.sync import TelegramClient
from telethon.tl.functions.messages import SendMediaRequest, SendMessageRequest
from telethon.tl.types import InputPeerUser
from telethon.errors import SessionPasswordNeededError, PhoneNumberInvalidError, FloodWaitError, SlowModeWaitError

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RESET = "\033[0m"
BOLD = "\033[1m"

MESSAGE_DIR = 'daily_message/'
MESSAGE_FILE = MESSAGE_DIR + 'message.txt'
IMAGE_FILE = MESSAGE_DIR + 'meme.png'
LOG_FILE = MESSAGE_DIR + 'output.txt'
LAST_SENT_FILE = MESSAGE_DIR + 'last_sent.json'
COOLDOWN_FILE = MESSAGE_DIR + 'cooldown.json'

SLEEP_MIN = 5
SLEEP_MAX = 15


def load_config():
    config_file = os.environ.get('CONFIG_FILE', 'testconfig.json')
    with open(config_file, 'r') as f:
        return json.load(f)


def save_config(config):
    config_file = os.environ.get('CONFIG_FILE', 'testconfig.json')
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)


def get_cooldown():
    if os.path.exists(COOLDOWN_FILE):
        with open(COOLDOWN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('until', 0)
    return 0


def set_cooldown(retry_after):
    until = time.time() + retry_after
    with open(COOLDOWN_FILE, 'w') as f:
        json.dump({'until': until}, f)


def get_cooldown_remaining():
    cooldown_until = get_cooldown()
    remaining = cooldown_until - time.time()
    return max(0, remaining)


def format_cooldown():
    remaining = get_cooldown_remaining()
    if remaining <= 0:
        return ""
    mins = int(remaining // 60)
    secs = int(remaining % 60)
    return f" (cooldown: {mins}m {secs}s)"


def load_message():
    with open(MESSAGE_FILE, 'r') as f:
        return f.read().strip()


def get_last_sent():
    if os.path.exists(LAST_SENT_FILE):
        with open(LAST_SENT_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_last_sent(data):
    with open(LAST_SENT_FILE, 'w') as f:
        json.dump(data, f)


def get_total_sent_24h():
    last_sent = get_last_sent()
    cutoff = time.time() - (24 * 60 * 60)
    return sum(1 for ts in last_sent.values() if ts > cutoff)


def should_send_message(phone, target_username):
    last_sent = get_last_sent()
    key = f"{phone}_{target_username}"
    
    if key not in last_sent:
        return True
    
    last_time = last_sent[key]
    current_date = time.strftime('%Y-%m-%d')
    last_date = time.strftime('%Y-%m-%d', time.localtime(last_time))
    
    return current_date != last_date


def log_output(message):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")


async def send_dm_with_image(client, target_username, message, image_path):
    try:
        entity = await client.get_entity(target_username)
        await client.send_file(
            entity,
            image_path,
            caption=message
        )
        return True, "Sent with image"
    except Exception as e:
        return False, str(e)


async def send_dm_no_image(client, target_username, message):
    try:
        entity = await client.get_entity(target_username)
        await client.send_message(entity, message)
        return True, "Sent without image"
    except Exception as e:
        return False, str(e)


async def send_dm_for_account(phone, config, target_username, use_image=True):
    session_path = f"telethon_sessions/{phone}"
    tried_telethon = False
    
    while True:
        try:
            client = TelegramClient(session_path, config['api_id'], config['api_hash'])
            
            async def custom_phone():
                print(f"[CODE REQUESTED] Enter code for {phone}: ")
                return input(f"[CODE REQUESTED] Enter code for {phone}: ")
            
            await client.start(phone=phone, code_callback=custom_phone)
            
            if not await client.is_user_authorized():
                log_output(f"[{phone}] Not authorized, skipping")
                await client.disconnect()
                return False
            
            message = load_message()
            
            if use_image and os.path.exists(IMAGE_FILE):
                success, msg = await send_dm_with_image(client, target_username, message, IMAGE_FILE)
            else:
                success, msg = await send_dm_no_image(client, target_username, message)
            
            await client.disconnect()
            
            if "Too many requests" in msg or "Flood wait" in msg:
                log_output(f"[{phone}] Rate limit detected: {msg}, setting 30min cooldown")
                set_cooldown(1800)
                return 'cooldown'
            
            if success:
                last_sent = get_last_sent()
                last_sent[f"{phone}_{target_username}"] = time.time()
                save_last_sent(last_sent)
                log_output(f"[{phone}] Successfully sent DM to @{target_username}: {msg}")
            else:
                log_output(f"[{phone}] Failed to send DM: {msg}")
            
            return success
            
        except sqlite3.OperationalError as e:
            if not tried_telethon and os.path.exists(f"telethon_sessions/{phone}.session"):
                session_path = f"telethon_sessions/{phone}"
                tried_telethon = True
                continue
            else:
                log_output(f"[{phone}] Database error: {e}")
                return False
        except FloodWaitError as e:
            log_output(f"[{phone}] Flood wait: {e.seconds}s, setting cooldown")
            set_cooldown(max(e.seconds, 1800))
            return 'cooldown'
        except SlowModeWaitError as e:
            log_output(f"[{phone}] Slow mode: {e.seconds}s, setting cooldown")
            set_cooldown(max(e.seconds, 1800))
            return 'cooldown'
        except Exception as e:
            error_str = str(e)
            if "Too many requests" in error_str:
                log_output(f"[{phone}] Too many requests, setting 30min cooldown")
                set_cooldown(1800)
                return 'cooldown'
            log_output(f"[{phone}] Error: {e}")
            return False


async def run_daily_message(target_username, use_image=True):
    print(f"\n{BOLD}{CYAN}=== DAILY MESSAGE SENDER ==={RESET}")
    print(f"Target: @{target_username}")
    print(f"Use image: {use_image}")
    print(f"Image file exists: {os.path.exists(IMAGE_FILE)}")
    print()
    
    config = load_config()
    accounts = config.get('accounts', [])
    
    if not accounts:
        print(f"{RED}No accounts found in config{RESET}")
        return
    
    success_count = 0
    skip_count = 0
    cooldown_triggered = False
    
    for phone in accounts:
        if not should_send_message(phone, target_username):
            log_output(f"[{phone}] Already sent today, skipping")
            skip_count += 1
            continue
        
        print(f"Processing account {phone}...")
        result = await send_dm_for_account(phone, config, target_username, use_image)
        
        if result == 'cooldown':
            cooldown_triggered = True
            break
        
        if result:
            success_count += 1
        
        sleep_time = random.uniform(SLEEP_MIN, SLEEP_MAX)
        log_output(f"Sleeping {sleep_time:.1f}s before next account")
        time.sleep(sleep_time)
        
        if get_cooldown_remaining() > 0:
            cooldown_triggered = True
            break
    
    total_24h = get_total_sent_24h()
    
    print(f"\n{BOLD}{GREEN}=== COMPLETE ==={RESET}")
    if cooldown_triggered:
        remaining = get_cooldown_remaining()
        mins = int(remaining // 60)
        secs = int(remaining % 60)
        print(f"{YELLOW}Cooldown triggered! Please wait {mins}m {secs}s before sending again.{RESET}")
    print(f"Successfully sent to @{target_username}: {success_count}")
    print(f"Skipped (already sent today): {skip_count}")
    print(f"Total sent (last 24hrs): {total_24h}")
    print(f"Total accounts: {len(accounts)}")


def daily_message_menu():
    while True:
        cooldown_str = format_cooldown()
        print(f"\n{BOLD}Daily Message Sender:{RESET}")
        print(f"1. Send daily message (with image){cooldown_str}")
        print(f"2. Send daily message (text only){cooldown_str}")
        print("3. Check send status")
        print("4. Reset send status (force resend)")
        print("5. Set default target")
        print("0. Back")
        
        choice = input("Select option: ").strip()
        
        if choice in ['1', '2']:
            remaining = get_cooldown_remaining()
            if remaining > 0:
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                print(f"{RED}Cooldown active. Please wait {mins}m {secs}s before sending.{RESET}")
                continue
            
            config = load_config()
            default_target = config.get('daily_message_target', '').lstrip('@')
            
            target = input(f"Enter target username (without @) [default: {default_target}]: ").strip().lstrip('@')
            if not target:
                if default_target:
                    target = default_target
                else:
                    print("Invalid target username")
                    continue
            
            use_image = (choice == '1')
            if use_image and not os.path.exists(IMAGE_FILE):
                print(f"{YELLOW}Warning: Image file not found at {IMAGE_FILE}, will send text only{RESET}")
            
            asyncio.run(run_daily_message(target, use_image))
        
        elif choice == '3':
            last_sent = get_last_sent()
            print(f"\n{BOLD}Send status:{RESET}")
            if not last_sent:
                print("No messages sent yet")
            else:
                total_24h = get_total_sent_24h()
                print(f"Total sent (last 24hrs): {total_24h}")
                print(f"\nPer-account status:")
                for key, timestamp in last_sent.items():
                    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))
                    print(f"  {key}: {date}")
        
        elif choice == '4':
            confirm = input("This will reset all send status and cooldown. Continue? (y/n): ").strip().lower()
            if confirm == 'y':
                save_last_sent({})
                set_cooldown(0)
                print(f"{GREEN}Send status and cooldown reset{RESET}")
        
        elif choice == '5':
            config = load_config()
            current_default = config.get('daily_message_target', '').lstrip('@')
            new_target = input(f"Enter default target username (without @) [current: '{current_default}']: ").strip().lstrip('@')
            if new_target:
                config['daily_message_target'] = new_target
                save_config(config)
                print(f"{GREEN}Default target set to: {new_target}{RESET}")
            else:
                print("Target cannot be empty")
        
        elif choice == '0':
            break
        else:
            print("Invalid choice")


if __name__ == '__main__':
    daily_message_menu()
