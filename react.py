import logging
import os
import sys
import asyncio
import random
import json
from telethon import TelegramClient
from telethon import functions, types
from dotenv import load_dotenv
from telethon.tl.patched import Message
from time import sleep
import sqlite3

#####################################################################################################
#THIS WONT WORK IF YOU TRY WITH TOO MANY ACCOUNTS, IT BREAKS SOMEWHERE ABOVE 35 WITH DB LOCKED ERRORS
#####################################################################################################

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR)

# Load your configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

root_path = os.path.dirname(os.path.abspath(__file__))
folder_session = root_path + '/telethon_sessions/'

api_id = int(config['api_id'])
api_hash = config['api_hash']

accounts = config['accounts']

EMOJI_LIST = ['🔥', '👍', '🌭', '❤','😍', '👀', '👏','🤯','🎉']
GROUP_LINK = config["group_target"]
DELAY = 5

# Tracking file for reactions
TRACKING_FILE = 'reaction_tracking.json'

def load_reaction_tracking():
    """Load existing reaction tracking data"""
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_reaction_tracking(tracking_data):
    """Save reaction tracking data"""
    with open(TRACKING_FILE, 'w') as f:
        json.dump(tracking_data, f, indent=2)

def has_account_reacted(account_phone, message_id, group_id):
    """Check if account has already reacted to this message"""
    tracking = load_reaction_tracking()
    group_key = str(group_id)
    if group_key not in tracking:
        return False
    if str(message_id) not in tracking[group_key]:
        return False
    return account_phone in tracking[group_key][str(message_id)]

def mark_account_reacted(account_phone, message_id, group_id):
    """Mark that account has reacted to this message"""
    tracking = load_reaction_tracking()
    group_key = str(group_id)
    if group_key not in tracking:
        tracking[group_key] = {}
    if str(message_id) not in tracking[group_key]:
        tracking[group_key][str(message_id)] = []
    tracking[group_key][str(message_id)].append(account_phone)
    save_reaction_tracking(tracking)

def get_valid_session_path(phone):
    session_path = folder_session + phone
    if os.path.exists(session_path + ".session"):
        return session_path
    telethon_path = f"telethon_sessions/{phone}"
    if os.path.exists(telethon_path + ".session"):
        return telethon_path
    return None

# Original function to react to most recent message
async def react_with_account(phone, delay_between_accounts, position):
    session_path = get_valid_session_path(phone)
    if not session_path:
        print(f"[ERROR] No valid session found for {phone}")
        return

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
            
            entity = await client.get_entity(GROUP_LINK)
            
            # Each account performs exactly 1 reaction
            try:
                # Fetch only the most recent message
                message = await client.get_messages(entity, limit=1)

                if message:
                    await asyncio.sleep(position * delay_between_accounts)
                    chosen_emoji = random.choice(EMOJI_LIST)

                    await client(functions.messages.SendReactionRequest(
                        peer=entity,
                        msg_id=message[0].id,
                        big=True,
                        add_to_recent=True,
                        reaction=[types.ReactionEmoji(emoticon=chosen_emoji)]
                    ))
                    print(f"Account {phone} reacted to message {message[0].id} with {chosen_emoji}")
                    await asyncio.sleep(DELAY)
            except Exception as e:
                logging.error(repr(e))
            
            await client.disconnect()
            break  # Success, exit loop
            
        except sqlite3.OperationalError as e:
            if not tried_telethon and os.path.exists(f"telethon_sessions/{phone}.session"):
                print(f"[WARN] Session error for {phone} at {session_path}, trying telethon_sessions/{phone}.session instead.")
                session_path = f"telethon_sessions/{phone}"
                tried_telethon = True
                continue
            else:
                print(f"[ERROR] Exception for account {phone}: {e}")
                break
        except Exception as e:
            print(f"[ERROR] Exception for account {phone}: {e}")
            break

# New function to react to specific users' posts
async def react_to_user_posts(phone, target_users, min_reactions, max_reactions, delay_between_accounts, position):
    session_path = get_valid_session_path(phone)
    if not session_path:
        print(f"[ERROR] No valid session found for {phone}")
        return

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
            
            entity = await client.get_entity(GROUP_LINK)
            group_id = entity.id
            
            try:
                # Get recent messages (last 10 to scan for target users)
                messages = await client.get_messages(entity, limit=10)
                
                for message in messages:
                    # Check if message is from a target user
                    if hasattr(message, 'sender_id') and message.sender_id:
                        sender = await client.get_entity(message.sender_id)
                        if hasattr(sender, 'username') and sender.username in target_users:
                            # Check if this account has already reacted to this message
                            if has_account_reacted(phone, message.id, group_id):
                                print(f"Account {phone} already reacted to message {message.id}, skipping")
                                continue
                            
                            # 50% chance to react to this post
                            if random.random() < 0.5:
                                # Random number of reactions between min and max
                                num_reactions = random.randint(min_reactions, max_reactions)
                                
                                await asyncio.sleep(position * delay_between_accounts)
                                
                                for _ in range(num_reactions):
                                    chosen_emoji = random.choice(EMOJI_LIST)
                                    await client(functions.messages.SendReactionRequest(
                                        peer=entity,
                                        msg_id=message.id,
                                        big=True,
                                        add_to_recent=True,
                                        reaction=[types.ReactionEmoji(emoticon=chosen_emoji)]
                                    ))
                                    print(f"Account {phone} reacted {chosen_emoji} to {sender.username}'s message {message.id} ({num_reactions} reactions)")
                                    await asyncio.sleep(random.uniform(1, 3))  # Small delay between reactions
                                
                                # Mark this account as having reacted to this message
                                mark_account_reacted(phone, message.id, group_id)
                                
                                await asyncio.sleep(DELAY)
                                break  # Only react to one post per account to avoid spam
                                
            except Exception as e:
                logging.error(repr(e))
            
            await client.disconnect()
            break  # Success, exit loop
            
        except sqlite3.OperationalError as e:
            if not tried_telethon and os.path.exists(f"telethon_sessions/{phone}.session"):
                print(f"[WARN] Session error for {phone} at {session_path}, trying telethon_sessions/{phone}.session instead.")
                session_path = f"telethon_sessions/{phone}"
                tried_telethon = True
                continue
            else:
                print(f"[ERROR] Exception for account {phone}: {e}")
                break
        except Exception as e:
            print(f"[ERROR] Exception for account {phone}: {e}")
            break

# Main menu and execution
def main():
    print("\n=== REACTION BOT MENU ===")
    print("1: React X number of times to the most recent message")
    print("2: React to specific users' posts (50% chance, X-Y reactions per post)")
    
    choice = input("\nEnter your choice (1 or 2): ").strip()
    
    if choice == '1':
        total_reactions = int(input("Enter the number of reactions to perform: "))
        accounts_to_use = accounts[:total_reactions]
        print(f"Using {len(accounts_to_use)} accounts to perform {total_reactions} reactions (1 reaction per account)")
        tasks = []
        for position, phone in enumerate(accounts_to_use):
            task = react_with_account(phone, 5, position)
            tasks.append(task)
        asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
        print("[INFO] All reactions done.")
        # Exit after one round
        return
    elif choice == '2':
        # Load config file path
        config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        # Check for saved values
        saved_users = config_data.get('target_usernames', [])
        saved_min = config_data.get('min_reactions', None)
        saved_max = config_data.get('max_reactions', None)
        saved_num = config_data.get('num_accounts', None)
        if saved_users and saved_min is not None and saved_max is not None and saved_num is not None:
            print(f"\nSaved target usernames: {saved_users}")
            print(f"Saved min reactions: {saved_min}")
            print(f"Saved max reactions: {saved_max}")
            print(f"Saved number of accounts: {saved_num}")
            print("1 - Use these values and skip prompts")
            print("2 - Enter new values (will overwrite saved values)")
            use_saved = input("Enter 1 or 2: ").strip()
        else:
            use_saved = '2'
        if use_saved == '1':
            target_users = saved_users
            min_reactions = saved_min
            max_reactions = saved_max
            num_accounts = saved_num
        else:
            print("\nEnter target usernames (without @) separated by commas:")
            target_users_input = input("Example: user1,user2,user3: ").strip()
            target_users = [user.strip() for user in target_users_input.split(',') if user.strip()]
            min_reactions = int(input("Enter minimum number of reactions per post: "))
            max_reactions = int(input("Enter maximum number of reactions per post: "))
            num_accounts = int(input("Enter number of accounts to use: "))
            # Save to config
            config_data['target_usernames'] = target_users
            config_data['min_reactions'] = min_reactions
            config_data['max_reactions'] = max_reactions
            config_data['num_accounts'] = num_accounts
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            print(f"[INFO] Saved new values to {config_file}")
        accounts_to_use = accounts[:num_accounts]
        print(f"Using {len(accounts_to_use)} accounts to react to posts from: {target_users}")
        print(f"50% chance per post, {min_reactions}-{max_reactions} reactions per post")
        print(f"Scanning last 10 messages, tracking reactions in {TRACKING_FILE}")
        while True:
            tasks = []
            for position, phone in enumerate(accounts_to_use):
                task = react_to_user_posts(phone, target_users, min_reactions, max_reactions, 5, position)
                tasks.append(task)
            asyncio.get_event_loop().run_until_complete(asyncio.gather(*tasks))
            print("[INFO] All reactions done. Waiting 10 seconds before next round...")
            sleep(10)
    else:
        print("Invalid choice. Please run the script again.")

if __name__ == "__main__":
    main()