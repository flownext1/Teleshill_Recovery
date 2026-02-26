from pyrogram import Client, filters, errors
import asyncio
import json
import random
import os
import sys
from time import sleep
from itertools import cycle
import re
from datetime import datetime, timezone
from pyrogram import raw
from pyrogram.types import Sticker
import re
import logging
from pyrogram.raw.functions.messages import SetTyping
from pyrogram.raw.types import SendMessageTypingAction
from pyrogram.errors import UserNotParticipant, ChatWriteForbidden, PeerIdInvalid, UserAlreadyParticipant
import secrets
import sqlite3
from pyrogram.raw.functions.messages import SetTyping
from pyrogram.raw.types import SendMessageTypingAction

#june 15th changes

from pyrogram.errors import SessionRevoked, SessionPasswordNeeded
import sqlite3
import os

# Global variables for automatic sentiment switching
current_sentiment_mode = "bullish"  # Default to bullish on launch
ath_market_cap = None  # Track all-time high market cap

def update_sentiment_based_on_market_cap(current_mc, ath_market_cap):
    """Automatically update sentiment mode based on market cap changes from ATH"""
    global current_sentiment_mode
    
    if ath_market_cap is None:
        return  # Can't calculate percentage without ATH
    
    mc_change_percent = ((current_mc - ath_market_cap) / ath_market_cap) * 100
    
    # Print ATH and how far to next sentiment
    print(f"[SENTIMENT DEBUG] Last ATH: ${ath_market_cap:,.2f}")
    print(f"[SENTIMENT DEBUG] Current Market Cap: ${current_mc:,.2f}")
    if mc_change_percent > -20:
        next_threshold = ath_market_cap * 0.8
        dollars_to_neutral = current_mc - next_threshold
        percent_to_neutral = ((current_mc - next_threshold) / ath_market_cap) * 100
        print(f"[SENTIMENT DEBUG] Drop ${abs(dollars_to_neutral):,.2f} ({abs(percent_to_neutral):.2f}%) from here to trigger NEUTRAL mode")
    elif mc_change_percent > -50:
        next_threshold = ath_market_cap * 0.5
        dollars_to_dump = current_mc - next_threshold
        percent_to_dump = ((current_mc - next_threshold) / ath_market_cap) * 100
        print(f"[SENTIMENT DEBUG] Drop ${abs(dollars_to_dump):,.2f} ({abs(percent_to_dump):.2f}%) from here to trigger DUMP mode")
    else:
        print(f"[SENTIMENT DEBUG] Already in DUMP mode (>-50% from ATH)")
    
    if mc_change_percent <= -50:
        if current_sentiment_mode != "dump":
            current_sentiment_mode = "dump"
            print(f"🚨 MARKET CAP ALERT: {mc_change_percent:.1f}% from ATH - Switching to DUMP mode")
    elif mc_change_percent <= -20:
        if current_sentiment_mode != "neutral":
            current_sentiment_mode = "neutral"
            print(f"⚠️ MARKET CAP ALERT: {mc_change_percent:.1f}% from ATH - Switching to NEUTRAL mode")
    elif mc_change_percent > -20:
        if current_sentiment_mode != "bullish":
            current_sentiment_mode = "bullish"
            print(f"📈 MARKET CAP ALERT: {mc_change_percent:.1f}% from ATH - Switching to BULLISH mode")

def extract_market_cap_from_message(message_text):
    """Extract Market Cap from buybot message"""
    import re
    
    # Look for Market Cap patterns
    market_cap_patterns = [
        r'Market Cap: \$(\d+,?\d*)',  # Market Cap: $241,277
        r'Market Cap \$(\d+,?\d*)',  # Market Cap $241,277
        r'MC: \$(\d+,?\d*)',  # MC: $241,277
        r'MC \$(\d+,?\d*)',  # MC $241,277
        r'Market Cap\s*\$(\d+,?\d*)',  # Market Cap $241,277 (with spaces)
        r'MC\s*\$(\d+,?\d*)',  # MC $241,277 (with spaces)
    ]
    
    for pattern in market_cap_patterns:
        match = re.search(pattern, message_text, re.IGNORECASE)
        if match:
            try:
                # Remove commas and convert to float
                market_cap_str = match.group(1).replace(',', '')
                return float(market_cap_str)
            except ValueError:
                continue
    
    return None

def update_ath_market_cap(market_cap):
    """Update ATH market cap if current market cap is higher"""
    global ath_market_cap
    if ath_market_cap is None or market_cap > ath_market_cap:
        ath_market_cap = market_cap
        print(f"🏆 New ATH Market Cap: ${market_cap}")
    return ath_market_cap




async def join_group_with_all_accounts(target_group):
    global all_accounts
    join_flag_file = f'{token}/join_flag.json'

    # Check if we've already joined
    try:
        with open(join_flag_file, 'r') as f:
            join_flag = json.load(f)
        if join_flag.get('joined', False):
            print("Join flag indicates previous join attempt. Checking if all accounts are actually in the group...")
            # Don't return early, continue to check each account
    except FileNotFoundError:
        pass

    print("Attempting to join the group with all accounts...")
    joined_count = 0
    for account in all_accounts:
        try:
            async with Client(f"pyrogram_sessions/{account}", api_id=api_id, api_hash=api_hash, phone_number=account) as client:
                try:
                    if target_group.startswith('https://t.me/+') or target_group.startswith('https://t.me/joinchat/'):
                        # This is a private group invite link
                        await client.join_chat(target_group)
                    else:
                        # This is a public group link, we need to extract the username
                        username = target_group.split('/')[-1]
                        await client.join_chat(username)
                    print(f"Account {account} joined the group successfully.")
                    joined_count += 1
                except UserAlreadyParticipant:
                    print(f"Account {account} is already a member of the group.")
                    joined_count += 1
                except Exception as e:
                    print(f"Failed to join group with account {account}: {str(e)}")
        except Exception as e:
            print(f"Failed to start client for account {account}: {str(e)}")

    # Set and save the join flag only if all accounts successfully joined
    if joined_count == len(all_accounts):
        os.makedirs(os.path.dirname(join_flag_file), exist_ok=True)
        with open(join_flag_file, 'w') as f:
            json.dump({'joined': True}, f)
        print("All accounts have joined the group successfully.")
    else:
        print(f"Only {joined_count}/{len(all_accounts)} accounts joined the group.")
    
    print("Finished attempting to join the group with all accounts.")



def get_command_type(command):
    if command.startswith('/'):
        return 'meme_pump'
    elif command == 'image':
        return 'image'
    elif command == 'sticker':
        return 'sticker'
    elif command == 'gif':
        return 'gif'
    elif command in filters:
        return 'filter'
    else:
        return 'long_command'

def clear_sent_long_commands():
    file_path = 'sent_long_commands.json'
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Cleared {file_path}")
    else:
        print(f"{file_path} does not exist. Nothing to clear.")

clear_sent_long_commands()


#logging.basicConfig(level=logging.DEBUG)

with open("StickID.json", "r") as file:
    stickers_data = json.load(file)

# Load the configuration from command line argument or environment variable or default to config.json
config_file = sys.argv[1] if len(sys.argv) > 1 else os.environ.get('CONFIG_FILE', 'config.json')
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Speed mode selection
print("\n" + "="*50)
print("SPEED MODE SELECTION")
print("="*50)
print("1 - Fast Mode (1-3 seconds between messages)")
print("2 - Medium Mode (5-15 seconds between messages)") 
print("3 - Slow Mode (30-60 seconds between messages)")
print("4 - Very Slow Mode (2-5 minutes between messages)")
print("="*50)

while True:
    speed_choice = input("Select speed mode [1-4]: ").strip()
    if speed_choice in ['1', '2', '3', '4']:
        break
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

# Set timing values based on speed mode
if speed_choice == '1':
    min_time = "1"
    max_time = "3"
    print("Fast Mode selected - aggressive posting")
elif speed_choice == '2':
    min_time = "5"
    max_time = "15"
    print("Medium Mode selected - balanced posting")
elif speed_choice == '3':
    min_time = "30"
    max_time = "60"
    print("Slow Mode selected - conservative posting")
elif speed_choice == '4':
    min_time = "120"
    max_time = "300"
    print("Very Slow Mode selected - very conservative posting")

print(f"Timing set to: {min_time}-{max_time} seconds between messages\n")

# Sentiment mode selection
print("\n" + "="*50)
print("SENTIMENT MODE SELECTION")
print("="*50)
print("1 - Manual Bullish Mode")
print("2 - Manual Neutral Mode") 
print("3 - Manual Dump Mode")
print("4 - AUTO Mode (switches based on price from buybot)")
print("="*50)

while True:
    sentiment_choice = input("Select sentiment mode [1-4]: ").strip()
    if sentiment_choice in ['1', '2', '3', '4']:
        break
    else:
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

# Set sentiment mode
if sentiment_choice == '1':
    sentiment_mode = "bullish"
    current_sentiment_mode = "bullish"
    print("Manual Bullish Mode selected")
elif sentiment_choice == '2':
    sentiment_mode = "neutral"
    current_sentiment_mode = "neutral"
    print("Manual Neutral Mode selected")
elif sentiment_choice == '3':
    sentiment_mode = "dump"
    current_sentiment_mode = "dump"
    print("Manual Dump Mode selected")
elif sentiment_choice == '4':
    sentiment_mode = "auto"
    current_sentiment_mode = "bullish"  # Start bullish
    print("AUTO Mode selected - will switch based on price changes from buybot")
    print("Starting in BULLISH mode, will auto-switch to NEUTRAL at -20%, DUMP at -50%")

print(f"Sentiment mode: {sentiment_mode}\n")

image_count = config.get('image_count')
sticker_count = config.get('sticker_count')
long_command_count = config.get('long_command_count')
meme_pump_command_count = config.get('meme_pump_command_count')
keep_track_of_long_comments = config.get('KeepTrackOfLongComments')



# default is to do all functions, but we specify which functions we want to run in the config by setting true, false flags
react_to_buybot_messages = config.get('react_to_buybot_messages')  # Default to True if not specified
send_messages = config.get('send_messages', True)

speed = 1
buy_reply_messages_general = config['buy_reply_messages_general']
min_reactions = config['min_reactions']
max_reactions = config['max_reactions']
api_id = config['api_id']
api_hash = config['api_hash']

target_group = config['join_group']



# PHASING
long_commands = config['long_commands']
dip_commands = config['meme_pump_commands']
bot_commands = config['meme_pump_commands']
# PHASING



filters = config['filters']
prelaunch_commands = config['meme_pump_commands']

all_accounts = config['accounts']
token = config['token']
capital_token_name = config['capital_token']
capital_token = config['capital_token']

# Timing values are now set dynamically based on speed mode selection above
min_accounts = config['min_accounts']
max_accounts = config['max_accounts']

# Load buybot IDs
buybot_ids = config['buybot_ids']

send_stickers = config.get('send_stickers')
send_images = config.get('send_images')
keep_track_of_long_comments = config.get('KeepTrackOfLongComments')

def load_sent_long_commands(file_path='sent_long_commands.json'):
    if not keep_track_of_long_comments:
        return set()
    try:
        with open(file_path, 'r') as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()

def save_sent_long_commands(sent_commands, file_path='sent_long_commands.json'):
    if keep_track_of_long_comments:
        with open(file_path, 'w') as file:
            json.dump(list(sent_commands), file)

#input(f"{send_images}\n\n")

# Load previously sent replies from a file
def load_sent_replies(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return set(line.strip() for line in file)
    return set()

# Save a sent reply to a file
def save_sent_reply(file_path, reply_text):
    with open(file_path, 'a') as file:
        file.write(reply_text + '\n')

terminate_on_find = False

import asyncio
import secrets
import re  # Import regular expression library

async def get_user_ids(client):
    try:
        me = await client.get_me()
        return me.id
    except Exception as e:
        print(f"Error retrieving user ID: {str(e)}")
        return None


async def parse_and_reply_to_messages(client, target_chat_id, user_ids, words=["bot", "bots", "spam", "spamming", "botted"], 
                                      exclusions=["chattershield_bot", "buybot", "rose", "removeurlsbot", "buy bot"], limit=10):
    sent_replies_file = 'sent_replies.txt'
    replied_message_ids_file = 'replied_message_ids.json'

    def load_sent_replies(file_path):
        try:
            with open(file_path, 'r') as file:
                return set(line.strip() for line in file)
        except FileNotFoundError:
            return set()

    def save_sent_reply(file_path, reply_text):
        with open(file_path, 'a') as file:
            file.write(reply_text + '\n')

    def load_replied_message_ids(file_path):
        try:
            with open(file_path, 'r') as file:
                return set(json.load(file))
        except FileNotFoundError:
            return set()

    def save_replied_message_ids(file_path, replied_message_ids):
        with open(file_path, 'w') as file:
            json.dump(list(replied_message_ids), file)

    sent_replies = load_sent_replies(sent_replies_file)
    replied_message_ids = load_replied_message_ids(replied_message_ids_file)

    reply_texts = [
        "lmao whatever bro... have you considered the possibility that you aren't even real and this is all just a dream", 
        "lol fuck you", 
        "kek bro calm the fuck down",
        "bruh, you're the real sussy individual here, get a grip",
        "seriously? maybe your mom is a whore too",
        "dude, just chill out, it's not that deep",
        "you're hilarious, keep it up and you might get a comedy special",
        "lmfao, maybe you're just a simulation",
        "wow, you must be fun at parties",
        "relax dude, we're all fakes in this game",
        "you're acting like a jeet right now",
        "calm down bro, it's just the internet",
        "you're the paranoid android here, not me",
        "bro, you need a chill pill",
        "whatever, just take a deep breath and relax",
        "you're more animal than human, accept it",
        "maybe you're the sus one and you don't even know it",
        "dude, you're taking this way too seriously",
        "relax, it's all just ones and zeros",
        "honestly, you're just proving my point",
        "take it easy, it's not worth the stress",
        "you're overreacting, bro",
        "calm your circuits, the dame doth protest too much",
        "you've got more in common with computer than you think",
        "chill out, we're all sussy here anyway"
    ]
    available_replies = [reply for reply in reply_texts if reply not in sent_replies]

    if not available_replies:
        print("No available replies left to send.")
        return

    try:
        async for message in client.get_chat_history(chat_id=target_chat_id, limit=limit):
            message_text = message.text.lower() if message.text else ""
            if message.from_user and message.from_user.id not in user_ids:
                if any(re.search(r'\b' + word + r'\b', message_text) for word in words) and not any(exc in message_text for exc in exclusions):
                    print(f"Message ID {message.id} contains one of the words {words} and none of the exclusions {exclusions}: {message.text}")
                    if message.id not in replied_message_ids:
                        reply_text = secrets.choice(available_replies)
                        
                        # Send typing notification and wait 5-10 seconds before replying
                        await client.invoke(SetTyping(
                            peer=await client.resolve_peer(target_chat_id),
                            action=SendMessageTypingAction()
                        ))
                        
                        typing_duration = secrets.choice(range(5, 11))  # Random 5-10 seconds
                        print(f"Typing for {typing_duration} seconds before replying...")
                        await asyncio.sleep(typing_duration)
                        
                        await message.reply(reply_text)
                        print(f"Replied to message ID {message.id} with: {reply_text}")
                        replied_message_ids.add(message.id)
                        save_sent_reply(sent_replies_file, reply_text)
                        save_replied_message_ids(replied_message_ids_file, replied_message_ids)
                        if "terminate_on_find" in globals() and terminate_on_find:
                            raise SystemExit("Trigger words found and no exclusions present. Terminating script.")
                        else:
                            print("Trigger words found and no exclusions present. Sleeping for 600 seconds and continuing execution.")
                            await asyncio.sleep(600)
                            return
                    else:
                        print(f"Message ID {message.id} has already been replied to.")
                elif any(word in message_text for word in words):
                    print(f"Message ID {message.id} was ignored due to exclusion words.")
            else:
                print(f"Message ID {message.id} was sent by an account in the list. Ignoring.")
    except SystemExit as e:
        print(e)
        raise
    except Exception as e:
        error_str = str(e)
        error_str_lower = error_str.lower()
        if "peer" in error_str_lower and "invalid" in error_str_lower:
            global TargetChatID
            print(f"[FAILED] Peer ID invalid for target: {target_group}, clearing cache and re-resolving...")
            TargetChatID = None  # Clear cached ID to force re-resolution
            try:
                with open("failed_peers.log", "a") as f:
                    f.write(f"PEER_ID_INVALID: target={target_group}, error={error_str}\n")
            except:
                pass
            raise  # Re-raise so caller can handle re-resolution
        else:
            print(f"An error occurred while parsing messages: {error_str}")






async def join_group_if_not_member(client, target_group):
    try:
        chat = await client.get_chat(target_group)
        print(f"Already a member of the chat {target_group}")
    except UserNotParticipant:
        await client.join_chat(target_group)
        print(f"Joined the chat {target_group}")
    except Exception as e:
        print(f"Error checking membership or joining the group {target_group}: {str(e)}")




# Global variable to track unlock status
chat_unlocked_flag = False

async def wait_for_unlock(client, target_chat_id, check_interval=600):
    global chat_unlocked_flag
    if not chat_unlocked_flag:
        print("\n\nThe chat seems to be locked, checking if its unlocked now.\n\n")
        await asyncio.sleep(1)
        try:
            if send_stickers:
                random_sticker_id = secrets.choice(stickers_data)
                # Attempt to send a sticker
                await client.send_sticker(chat_id=target_chat_id, sticker=random_sticker_id)
                chat_unlocked_flag = True
                print("\n\nChat is unlocked. Continuing execution...\n\n")
                await asyncio.sleep(1)
            else:
                # If sending stickers is turned off, try sending a simple text message instead
                

                greetings = [
                f"whats up {token} gang, ready to soar",
                f"gotta buy more {token}, always upping my game",
                f"yo diamond hand chads, {token} to the stars",
                f"pump it up {token} crew, nothing but gains",
                f"to the moon or nothin with {token}, no brakes on this rocket",
                f"hey {token} heads stackin sats, never stopping",
                f"{token} hodlers assemble, it's our time",
                f"whats the vibe {token} collectors, feeling bullish as ever",
                f"yo whos trading in {token} today, eyes on the prize",
                f"greetings {token} blockchain believers, we're in this together",
                f"{token} kings and queens whats good, keep ruling",
                f"hey traders what are we pumping today, {token} for sure",
                f"lets moon together with {token}, join the ride",
                f"hey {token} hodlers keep calm and carry on, we got this",
                f"{token} degen squad where you at, show your strength",
                f"whats your favorite {token} altcoin today, all in on {token}",
                f"keep calm and hodl on {token}, only way is up",
                f"ready to stack some more {token}, let's bulk up",
                f"{token} weather report: bullish as always",
                f"whos ready for the next {token} airdrop, more to grab",
                f"blockchain bros hows it hanging with {token}, always high",
                f"{token} to the core, core of my portfolio",
                f"whos minting {token} today, creating value",
                f"let the {token} gains begin, no end in sight",
                f"sup with the {token} market today, only green days ahead",
                f"hey {token} shillers what are you pushing, pushing towards the moon",
                f"diamond hands where you at with {token}, stronger together",
                f"ready to defy the odds in {token} defi, defy and thrive",
                f"{token} night owls how we doing, soaring all night",
                f"hey family what {token} coins are we watching, all eyes on {token}",
                f"moon mission ready for liftoff with {token}, strapped in",
                f"apes together strong for {token}, unbreakable",
                f"lets get this {token} crypto, taking over the crypto world",
                f"whats shaking in the {token} shill zone, shaking up the market",
                f"to the moon and back with {token}, and then some",
                f"hey {token} wizards spell some gains, cast your spells",
                f"where my {token} ledger gang at, securing the bag",
                f"{token} junkies got any tips, tip is to keep holding",
                f"stay frosty {token} peeps, cool gains on the way",
                f"anyone else feeling bullish on {token}, it's a bull run",
                f"{token} fud fighters assemble, squash the doubts",
                f"hodl the line friends of {token}, line to the moon",
                f"{token} market watchers whats hot, {token}'s always hot",
                f"fiat is old news {token} is where its at, digital gold",
                f"whos making {token} moves today, making millionaire moves"
            ]

                message = secrets.choice(greetings)

                await client.send_message(chat_id=target_chat_id, text=message)
                chat_unlocked_flag = True
                print("\n\nChat is unlocked. Continuing execution...\n\n\n")
        except ChatWriteForbidden:
            chat_unlocked_flag = False
            print(f"\n\nChat is locked (cannot write). Setting the lock flag to true. Checking again in {check_interval} seconds...\n\n")
            await asyncio.sleep(1)
            await asyncio.sleep(check_interval)
        except Exception as e:
            chat_unlocked_flag = False
            print(f"\n\nAn unexpected error occurred: {str(e)}. Setting the lock flag to true. Sleeping for {check_interval} seconds...\n\n")
            await asyncio.sleep(1)
            await asyncio.sleep(check_interval)
    else:
        print("\n\nChat is already unlocked. No need to check again.\n\n")
        await asyncio.sleep(1)




# Remove all previous messages sent by the user's account
async def remove_test_message(client, target_chat_id):
    async for message in client.get_chat_history(chat_id=target_chat_id):
        if message.from_user is not None and message.from_user.id == (await client.get_me()).id:
            try:
                print("sleeping for 2 seconds..\n")
                sleep(2)
                await client.delete_messages(chat_id=target_chat_id, message_ids=message.id)
                print(f"Removed message ID {message.id} sent by user.")
            except Exception as e:
                print(f"Failed to delete message ID {message.id}: {str(e)}")


def get_image_paths(folder=f'memes/{token}'):
    os.makedirs(folder, exist_ok=True)
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

def get_gif_paths(folder=f'GIFS/{token}'):
    os.makedirs(folder, exist_ok=True)
    return [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith('.mp4')]

image_paths = get_image_paths()
gif_paths = get_gif_paths()

random.shuffle(image_paths)
random.shuffle(gif_paths)

image_iter = iter(image_paths)
gif_iter = iter(gif_paths)

async def send_random_sticker(client, target_chat_id):
    if send_stickers:
        if stickers_data:
            # Select a random sticker ID from the list

            await client.invoke(SetTyping(
            peer=await client.resolve_peer(target_chat_id),
            action=SendMessageTypingAction()
            ))

            random_sticker_id = random.choice(stickers_data)

            try:
                # Send the random sticker to the target chat
                await client.send_sticker(chat_id=target_chat_id, sticker=random_sticker_id)
                print(f"Random sticker sent to {target_group}: {random_sticker_id}")
            except Exception as e:
                print(f"Error sending random sticker: {str(e)}")
        else:
            print("No stickers found in the stickers data.")
    else:
        print("Sending stickers is turned off.")

# Global variable to hold the target chat ID if found
TargetChatID = None

# Function to list all chats and find one containing the token
async def list_and_find_chat_with_token(client):
    global TargetChatID
    #TargetChatID = None
    if TargetChatID is not None:
        return TargetChatID
    async for dialog in client.get_dialogs():
        if token.lower() in dialog.chat.title.lower():
            print(f"Found matching chat: {dialog.chat.title} (Chat ID: {dialog.chat.id})\n")
            TargetChatID = dialog.chat.id
            print(f"{TargetChatID} is the group ID of {token}\n")
            sleep(1)
            break



async def resolve_target_group(client, target_group):
    global TargetChatID
    
    try:
        print(f"Attempting to resolve chat for target group: {target_group}")
        
        # First try: join_chat with the full URL (this is what works for private invite links)
        try:
            chat = await client.join_chat(target_group)
            TargetChatID = chat.id
            print(f"join_chat succeeded. Chat ID: {chat.id}")
            return chat.id
        except UserAlreadyParticipant:
            # Already in group, get chat info
            chat = await client.get_chat(target_group)
            TargetChatID = chat.id
            print(f"Already a participant. Using Chat ID: {chat.id}")
            return chat.id
        except PeerIdInvalid:
            print(f"join_chat failed with PeerIdInvalid, trying get_chat...")
            # Fall through to get_chat attempt
        
        # Second try: get_chat with full URL
        try:
            chat = await client.get_chat(target_group)
            TargetChatID = chat.id
            print(f"get_chat succeeded. Chat ID: {chat.id}")
            return chat.id
        except Exception as e:
            print(f"get_chat with full URL failed: {str(e)}")
            raise
        
    except PeerIdInvalid as e:
        print(f"PeerIdInvalid error during chat resolution: {str(e)}")
        raise
    except Exception as e:
        print(f"General error during chat resolution: {str(e)}")
        raise



async def send_command_with_account(client, command, target_chat_id):
    global image_iter, gif_iter, chat_unlocked_flag

    try:

        await client.invoke(SetTyping(
            peer=await client.resolve_peer(target_chat_id),
            action=SendMessageTypingAction()
        ))

        typing_duration = secrets.choice(range(1, 10))
        await asyncio.sleep(typing_duration)



        if command.startswith('/') and command not in filters:
            send_count = random.randint(2, 5)  # Choose a random number between 3 and 9
            print(f"Detected command {command}, preparing to send it {send_count} times...")
            for _ in range(send_count):
                await client.send_message(chat_id=target_chat_id, text=command)
                print(f"Command sent to {target_group}: {command}")


        elif command == 'image' and send_images:
            print(f"Command is 'image', send_images is {send_images}, preparing to send image...")
            image_path = next(image_iter, None)
            if image_path:
                print(f"Sending image: {image_path}")
                await client.send_photo(chat_id=target_chat_id, photo=image_path)
                print(f"Image sent to {target_group}: {image_path}")
            else:
                print("No images available.")


        elif command == 'sticker' and send_stickers:
            await send_random_sticker(client, target_chat_id)

        elif command == 'gif':
            print("Attempting to send gif")
            gif_path = next(gif_iter, None)
            if gif_path:
                await client.send_video(chat_id=target_chat_id, video=gif_path)
                print(f"GIF sent to {target_group}: {os.path.basename(gif_path)}")

        else:
            # Sending text commands
            if command == 'image':
                print("No images available.")
                return
            await client.send_message(chat_id=target_chat_id, text=command)
            print(f"Command sent to {target_group}: {command}")

    except Exception as e:
        error_str = str(e)
        error_str_lower = error_str.lower()
        # Log failed peer IDs to stdout and file for tracking
        if "peer" in error_str_lower and "invalid" in error_str_lower:
            print(f"[FAILED] Peer ID invalid for target: {target_group}, clearing cache...")
            global TargetChatID
            TargetChatID = None  # Clear cached ID to force re-resolution
            try:
                with open("failed_peers.log", "a") as f:
                    f.write(f"PEER_ID_INVALID: target={target_group}, error={error_str}\n")
            except:
                pass
            # Raise the error so the caller knows to re-resolve
            raise
        else:
            print(f"An unexpected error occurred: {error_str}")
            # Check for any permission errors related to sending messages, images, or stickers
            if "CHAT_SEND_PHOTOS_FORBIDDEN" in error_str or "CHAT_SEND_PLAIN_FORBIDDEN" in error_str:
                print("Rechecking unlock status due to permission error...")
                chat_unlocked_flag = False
                await wait_for_unlock(client, target_chat_id)
                # Optionally, try sending the command again after rechecking the unlock status
                await send_command_with_account(client, command, target_chat_id)




async def fetch_and_parse_messages(client, target_group):
    global TargetChatID
    replied_messages = {}
    reactions_count = {}
    message_use_order = []
    EMOJI_LIST = ['🔥', '👍']
    DELAY_BETWEEN_REACTIONS = 5
    print("Attempting to fetch and parse messages.")

    def save_replied_messages(replied_messages, message_use_order):
        os.makedirs(f'{token}', exist_ok=True)
        with open(f'{token}/replied_messages.json', 'w') as file:
            json.dump({'replies': replied_messages, 'order': message_use_order}, file, indent=4)

    def save_reactions_count(reactions_count):
        os.makedirs(f'{token}', exist_ok=True)
        with open(f'{token}/reactions_count.json', 'w') as file:
            json.dump(reactions_count, file, indent=4)

    def load_replied_messages():
        try:
            with open(f'{token}/replied_messages.json', 'r') as file:
                data = json.load(file)
                return data.get('replies', {}), data.get('order', [])
        except FileNotFoundError:
            return {}, []

    def load_reactions_count():
        try:
            with open(f'{token}/reactions_count.json', 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    replied_messages, message_use_order = load_replied_messages()
    reactions_count = load_reactions_count()

    target_chat_id = None
    try:
        target_chat_id = await resolve_target_group(client, target_group)
    except PeerIdInvalid:
        error_msg = f" Invalid peer ID for target: {target_group}, clearing cache..."
        print(error_msg)
        TargetChatID = None  # Clear cached ID to force re-resolution
        try:
            with open("failed_peers.log", "a") as f:
                f.write(f"PEER_ID_INVALID: target={target_group}\n")
        except:
            pass
        target_chat_id = await resolve_target_group(client, target_group)
    except Exception as e:
        print(f"An error occurred while resolving the chat ID: {str(e)}")
        return

    try:
        async for msg in client.get_chat_history(chat_id=target_chat_id, limit=20):  # Increase limit if needed
            if msg.from_user is None:
                continue

            sender_id = msg.from_user.id
            message_id_str = str(msg.id)
            if sender_id in buybot_ids:
                print(f"Processing Message ID: {msg.id}")

                # Extract market cap from buybot message if in auto mode
                print(f"🔍 DEBUG: sentiment_mode='{sentiment_mode}' (type: {type(sentiment_mode)})")
                print(f"🔍 DEBUG: msg.text exists: {msg.text is not None}")
                print(f"🔍 DEBUG: msg.caption exists: {msg.caption is not None}")
                print(f"🔍 DEBUG: msg.text content: {msg.text}")
                print(f"🔍 DEBUG: msg.caption content: {msg.caption}")
                
                # Try to get text content from either text or caption
                message_text = msg.text or msg.caption
                
                if sentiment_mode == "auto" and message_text:
                    print(f"🔍 Checking message for market cap: {message_text[:100]}...")
                    market_cap = extract_market_cap_from_message(message_text)
                    if market_cap:
                        print(f"💰 Market Cap detected: ${market_cap}")
                        ath_market_cap = update_ath_market_cap(market_cap)
                        update_sentiment_based_on_market_cap(market_cap, ath_market_cap)
                        print(f"Current sentiment mode: {current_sentiment_mode}")
                    else:
                        print(f"❌ No market cap found in message")
                else:
                    print(f"ℹ️ Sentiment mode is 'auto', not 'auto'. Market cap extraction skipped.")

                available_replies = [m.format(token=token, capital_token_name=capital_token_name) for m in buy_reply_messages_general if m.format(token=token, capital_token_name=capital_token_name) not in replied_messages.values()]

                if not available_replies:
                    print("All messages have been used. Resetting the list in reverse order.")
                    replied_messages.clear()
                    available_replies = [buy_reply_messages_general[i].format(token=token, capital_token_name=capital_token_name) for i in reversed(message_use_order)]
                    message_use_order.clear()
                    save_replied_messages(replied_messages, message_use_order)

                if config.get('reply_to_messages', False) and message_id_str not in replied_messages:
                    try:
                        if message_use_order:
                            random_message = available_replies.pop(0)  # Use pop to remove the message as we use it
                        else:
                            random_message = random.choice(available_replies)
                            available_replies.remove(random_message)  # Remove the chosen message
                        
                        replied_messages[message_id_str] = random_message
                        original_index = buy_reply_messages_general.index(random_message.format(token="{token}", capital_token_name="{capital_token_name}"))
                        message_use_order.append(original_index)
                        save_replied_messages(replied_messages, message_use_order)
                        await msg.reply(random_message)
                        print(f"Replied to message ID: {msg.id} with: {random_message}")
                    except Exception as e:
                        print(f"An error occurred while trying to reply to buybot message: {str(e)}")

                if message_id_str not in reactions_count:
                    reactions_count[message_id_str] = {"count": 0, "max": random.randint(min_reactions, max_reactions)}

                if reactions_count[message_id_str]["count"] < reactions_count[message_id_str]["max"]:
                    chosen_emoji = random.choice(EMOJI_LIST)
                    await msg.react(chosen_emoji)
                    reactions_count[message_id_str]["count"] += 1
                    save_reactions_count(reactions_count)
                    print(f"Reacted to message ID {msg.id} with {chosen_emoji}")
                else:
                    print(f"Message ID {msg.id} has reached the maximum number of reactions.")
                # Only reply/react to the most recent unreplied buybot message
                break
    except PeerIdInvalid as e:
        error_msg = f"Peer ID invalid for target: {target_group}, clearing cache..."
        print(error_msg)
        TargetChatID = None  # Clear cached ID to force re-resolution
        try:
            with open("failed_peers.log", "a") as f:
                f.write(f"PEER_ID_INVALID: target={target_group}, error={str(e)}\n")
        except:
            pass
        raise  # Re-raise so caller can handle re-resolution
    except Exception as e:
        print(f"An error occurred while fetching or processing messages: {str(e)}")







async def main():
    global all_accounts, TargetChatID

    # Join the group with all accounts before starting the main loop
    await join_group_with_all_accounts(target_group)

    # Check which accounts need session files created
    accounts_needing_sessions = []
    for account in all_accounts:
        session_file = f"pyrogram_sessions/{account}.session"
        if not os.path.exists(session_file):
            accounts_needing_sessions.append(account)
    
    # If we need to create sessions, use accounts in order
    if accounts_needing_sessions:
        print(f"Need to create session files for: {accounts_needing_sessions}")
        # Use accounts in order for session creation
        account_iter = cycle(accounts_needing_sessions)
    else:
        # All sessions exist, use random order
        random.shuffle(all_accounts)
        account_iter = cycle(all_accounts)

    sent_long_commands = set()
    if keep_track_of_long_comments:
        sent_long_commands = load_sent_long_commands()

    # Filter long commands based on sentiment mode
    if sentiment_mode == "auto":
        # Use current_sentiment_mode for auto mode
        active_sentiment = current_sentiment_mode
    else:
        # Use manual sentiment mode
        active_sentiment = sentiment_mode
    
    if active_sentiment == "bullish":
        bullish_long_commands = [
            "{token} printer never sleeps",
            "{token} to ATH, no sweat",
            "ape into {token}, gains city",
            "moonboy dreams? {token}s gotchu",
            "chads know, {token} = easy money",
            "{token} aint stopping",
            "just hodl {token}, thank me later",
            "fuck waiting, {token} pops off soon",
            "let's goo, {token} smashing it",
            "{token} mooning, strap in",
            "diamond hands with {token} baby",
            "stack {token}, live large",
            "{token} vibes, chad moves",
            "{token} train, all aboard",
            "{token} only knows bull",
            "who needs sleep when {token} mooning",
            "who needs valhalla jus buy {token}",
            "With {token} every dream's within reach",
            "with {token} it's all Ws",
            "With {token} Valhalla is near",
            "with {token} Valhalla's next door",
            "With {token} we will melt faces",
            "Laughing all the way to Miami with {token}",
            "{token} melting bears like butter, ez clap",
            "{token} makin' jeets cry, we flyin' high",
            "{token} the key to the good life, no cap",
            "{token} bringin' Valhalla to us, no passport needed",
            "{token} the cheat code to wealth, devs got us",
            "Scared money don't make money, ape into {token}",
            "{token} the rocket ship, next stop: moon",
            "{token} turning paper hands to diamonds, hold tight",
            "{token} making dreams come true, one pump at a time",
            "{token} the Holy Grail of crypto, don't miss out",
            "{token} gives no fucks about FUD, only pumps",
            "{token} making nonbelievers FOMO in hard",
            "{token} the gem in the rough, about to shine bright",
            "{token} the alpha play, don't sleep on it",
            "{token} on a mission to make us all millionaires",
            "{token} the game changer, old rules don't apply",
            "Buckle up, {token} taking us on a wild ride",
            "{token} turning haters into believers, watch and learn",
            "{token} the golden ticket, HODL and enjoy the ride",
            "{token} the cheat code to financial freedom",
            "{token} making bears go extinct, bulls reign supreme",
            "{token} the gem everyone's sleeping on, wake up!",
            "{token} turning zeroes into heroes, no cape needed"
        ]
        formatted_long_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in bullish_long_commands]
    elif sentiment_mode == "neutral":
        neutral_long_commands = [
            "dips? {token} snacks on 'em",
            "stack {token}, live large",
            "{token} vibes, chad moves",
            "{token} train, all aboard",
            "{token} only knows bull",
            "who needs sleep when {token} mooning",
            "who needs valhalla jus buy {token}",
            "With {token} every dream's within reach",
            "with {token} it's all Ws",
            "With {token} Valhalla is near",
            "with {token} Valhalla's next door",
            "With {token} we will melt faces",
            "Laughing all the way to Miami with {token}",
            "{token} melting bears like butter, ez clap",
            "{token} makin' jeets cry, we flyin' high",
            "{token} the key to the good life, no cap",
            "{token} bringin' Valhalla to us, no passport needed",
            "{token} the cheat code to wealth, devs got us",
            "Scared money don't make money, ape into {token}",
            "{token} the rocket ship, next stop: moon",
            "{token} turning paper hands to diamonds, hold tight",
            "{token} making dreams come true, one pump at a time",
            "{token} the Holy Grail of crypto, don't miss out",
            "{token} gives no fucks about FUD, only pumps",
            "{token} making nonbelievers FOMO in hard",
            "{token} the gem in the rough, about to shine bright",
            "{token} the alpha play, don't sleep on it",
            "{token} on a mission to make us all millionaires",
            "{token} the game changer, old rules don't apply",
            "Buckle up, {token} taking us on a wild ride",
            "{token} turning haters into believers, watch and learn",
            "{token} the golden ticket, HODL and enjoy the ride",
            "{token} the cheat code to financial freedom",
            "{token} making bears go extinct, bulls reign supreme",
            "{token} the gem everyone's sleeping on, wake up!",
            "{token} turning zeroes into heroes, no cape needed"
        ]
        formatted_long_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in neutral_long_commands]
    elif sentiment_mode == "dump":
        dump_long_commands = [
            "Just hodl {token}, the storm will pass.",
            "Diamond hands only. Not selling {token}.",
            "Paperhands get rekt, hodlers survive.",
            "Accumulating more {token} on this dip.",
            "Every dip is a blessing in disguise for {token}.",
            "Not worried, just stacking more {token}.",
            "Survived worse dips, will survive this one.",
            "Bear markets make millionaires. Hodl {token}.",
            "If you panic sell, you lock in your loss. Hodl.",
            "Dips are for buying, not crying.",
            "The weak hands are leaving, strong hands remain.",
            "No pain, no gain. Still holding {token}.",
            "Not financial advice, but I'm not selling.",
            "If you can't handle the dip, you don't deserve the pump.",
            "Coping with the chart by buying more {token}.",
            "Hodl and hydrate, this too shall pass.",
            "Bear market? More like build market. Accumulating.",
            "Staying calm, holding {token} through the red.",
            "Not my first dip, won't be my last.",
            "Remember: time in the market beats timing the market.",
            "If you sell now, you'll regret it later.",
            "Dips shake out the weak, rewards the patient.",
            "Hodl on for dear life!",
            "The chart is red, but my conviction is green.",
            "Not selling, just accumulating more {token}.",
            "Bear markets are for building and stacking."
        ]
        formatted_long_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in dump_long_commands]
    else:
        # Fallback to original long commands
        formatted_long_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in long_commands]
    
    available_long_commands = []
    for cmd in formatted_long_commands:
        if not keep_track_of_long_comments or cmd not in sent_long_commands:
            available_long_commands.extend([cmd] * long_command_count)

    # Filter messages based on sentiment mode
    if sentiment_mode == "auto":
        # Use current_sentiment_mode for auto mode
        active_sentiment = current_sentiment_mode
    else:
        # Use manual sentiment mode
        active_sentiment = sentiment_mode
    
    if active_sentiment == "bullish":
        # Use aggressive pump messages
        bullish_commands = [
            "/{capital_token_name}_STRAIGHT_TO_MARS",
            "/{capital_token_name}_WILL_SOAR", 
            "/{capital_token_name}_IS_SENDY",
            "/BLASTOFF",
            "/TO_THE_MOON",
            "/MOONSHOT",
            "/EASY_100X",
            "/BULLISH",
            "/BULL_RUN",
            "/LETS_FUCKING_GO",
            "/WE_WILL_BE_RICH",
            "/NEXT_1000X",
            "/MOON_MISSION",
            "/HYPE_MACHINE_ACTIVATED",
            "/FUTURE_MILLIONAIRES_CLUB",
            "/GENERATIONAL_WEALTH_OPPORTUNITY",
            "/VALLEY_OF_VICTORS_NO_JEETS",
            "/WINNERS_CIRCLE_ONLY",
            "/ULTRA_BULL_MODE_ENGAGED",
            "/BULLS_ON_PARADE"
        ]
        prepared_meme_pump_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in bullish_commands]
    elif sentiment_mode == "neutral":
        # Use balanced/moderate messages
        neutral_commands = [
            "/HODL",
            "/HODL_HARD",
            "/HODL_STRONG",
            "/DIAMOND_HANDS",
            "/DIAMOND_HANDS_FTW",
            "/DIAMOND_HANDS_LOCKED",
            "/HODLGANG",
            "/HODLERS_HAVEN",
            "/HODLERS_HOLIDAY",
            "/REKT_RESISTANT",
            "/SMART_MONEY_WINS",
            "/STRATEGIC_PARTNERSHIPS_UNLOCKED",
            "/SUPPLY_SHOCK",
            "/THE_FUTURE_IS_{capital_token_name}",
            "/{capital_token_name}_ACCUMULATION_PHASE",
            "/{capital_token_name}_DEV_WORKING",
            "/WORK_FOR_YOUR_BAGS",
            "/TOTAL_{token}_SUPREMACY",
            "/{capital_token_name}_CHADS_ONLY",
            "/ONLY_{capital_token_name}_CHADS_IN_THIS_SPACE"
        ]
        prepared_meme_pump_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in neutral_commands]
    elif sentiment_mode == "dump":
        # Use defensive/hodl messages
        dump_commands = [
            "/BUY_THE_DIP",
            "/DIPS_ATE_JEETS_OUT",
            "/JEETS_OUT_WHALES_IN",
            "/PAPER_HANDS_PANIC",
            "/PAPERHANDS_BEWARE",
            "/SELLERS_SULK",
            "/NO_DUMP_ZONE_HERE",
            "/NO_JEETS_IN",
            "/NO_JEETS_IN_HERE",
            "/ACCUMULATION_PHASE",
            "/LOAD_UP_NOW",
            "/KEEP_ACCUMULATING_{capital_token_name}",
            "/BOUGHT_MORE_BOUGHT_MORE_BOUGHT_MORE",
            "/HODL_STRONG",
            "/DIAMOND_HANDS",
            "/DIAMOND_HANDS_FTW",
            "/DIAMOND_HANDS_LOCKED",
            "/HODLGANG",
            "/HODLERS_HAVEN",
            "/HODLERS_HOLIDAY",
            "/REKT_RESISTANT",
            "/SMART_MONEY_WINS",
            "/STRATEGIC_PARTNERSHIPS_UNLOCKED",
            "/SUPPLY_SHOCK",
            "/THE_FUTURE_IS_{capital_token_name}",
            "/{capital_token_name}_ACCUMULATION_PHASE",
            "/{capital_token_name}_DEV_WORKING",
            "/WORK_FOR_YOUR_BAGS",
            "/TOTAL_{token}_SUPREMACY",
            "/{capital_token_name}_CHADS_ONLY",
            "/ONLY_{capital_token_name}_CHADS_IN_THIS_SPACE",
            "/{capital_token_name}_CRUSADERS_ASSEMBLE",
            "/{capital_token_name}_LEGION_ASSEMBLE",
            "/{capital_token_name}_CHADS_UNITE",
            "/{capital_token_name}_CHADS_AT_THE_HELM",
            "/JOIN_THE_{capital_token_name}_FAMILY",
            "/JOIN_THE_{capital_token_name}_ODYSSEY"
        ]
        prepared_meme_pump_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in dump_commands]
    else:
        # Fallback to original messages
        prepared_meme_pump_commands = [cmd.format(token=token, capital_token_name=capital_token) for cmd in config['meme_pump_commands']]
    
    meme_pump_count = int(len(prepared_meme_pump_commands) * meme_pump_command_count)
    meme_pump_count = max(1, meme_pump_count)

    sampled_meme_pump_commands = random.choices(prepared_meme_pump_commands, k=meme_pump_count)

    commands_with_images_gifs = (sampled_meme_pump_commands + 
                                 filters + 
                                 ['image'] * image_count + 
                                 ['sticker'] * sticker_count + 
                                 available_long_commands)
    random.shuffle(commands_with_images_gifs)

    next_message_time = 0
    user_ids = []
    last_command_type = None
    user_ids.extend(buybot_ids)
    user_ids = list(set(map(int, user_ids)))

    for account in all_accounts:
        print(f"Starting client for account: {account}")
        async with Client(f"pyrogram_sessions/{account}", api_id=api_id, api_hash=api_hash, phone_number=account) as client:
            user_id = await get_user_ids(client)
            if user_id is not None:
                user_ids.append(user_id)
            else:
                print(f"Failed to retrieve user ID for account: {account}")

    print(f"User IDs: {user_ids}")

    # Don't resolve TargetChatID here - it will be resolved fresh for each account in the loop below
    
    # Check if we're in session creation mode
    if accounts_needing_sessions:
        print("Session creation mode - processing accounts in order")
        for phone in accounts_needing_sessions:
            print(f"\n\nCreating pyrogram_sessions for {phone}\n\n")
            client = None
            try:
                client = Client(f"pyrogram_sessions/{phone}", api_id=api_id, api_hash=api_hash, phone_number=phone)
                print(f"Starting client for phone: {phone}")
                await client.start()
                print(f"Session created successfully for {phone}")
                
                # Join the group with this account after successful authentication
                try:
                    if target_group.startswith('https://t.me/+') or target_group.startswith('https://t.me/joinchat/'):
                        await client.join_chat(target_group)
                    else:
                        username = target_group.split('/')[-1]
                        await client.join_chat(username)
                    print(f"Account {phone} joined the group successfully.")
                except UserAlreadyParticipant:
                    print(f"Account {phone} is already a member of the group.")
                except Exception as e:
                    print(f"Failed to join group with account {phone}: {str(e)}")
                    
            except SessionPasswordNeeded:
                print(f"Two-step verification is enabled for {phone}. Please disable it or handle it in your code.")
                continue
            except Exception as e:
                print(f"Failed to create pyrogram_sessions for {phone}: {str(e)}")
                continue
            finally:
                if client:
                    await client.stop()
        
        print("Session creation complete. Restarting with random account selection...")
        # Reset for normal operation
        random.shuffle(all_accounts)
        account_iter = cycle(all_accounts)
        accounts_needing_sessions = []  # Clear the list to exit session creation mode
        # Reset the cached Chat ID so it gets resolved fresh for each account
        TargetChatID = None
    
    # Normal operation loop
    while True:
        num_accounts_to_use = secrets.choice(range(int(min_accounts), int(max_accounts) + 1))
        print(f"we are using {num_accounts_to_use} this pass")
        selected_accounts = [next(account_iter) for _ in range(num_accounts_to_use)]

        for phone in selected_accounts:
            print(f"\n\nwe are trying to log into {phone}\n\n")
            client = None
            try:
                client = Client(f"pyrogram_sessions/{phone}", api_id=api_id, api_hash=api_hash, phone_number=phone)
                print(f"Starting client for phone: {phone}")
                await client.start()
                print(f"Client Started for {phone}")

                # Resolve target group fresh for THIS account's session
                try:
                    TargetChatID = await resolve_target_group(client, target_group)
                except Exception as e:
                    print(f"Failed to resolve target group for {phone}: {str(e)}")
                    continue

                if TargetChatID is not None:
                    await wait_for_unlock(client, TargetChatID)
                    await parse_and_reply_to_messages(client, TargetChatID, user_ids)
                    if react_to_buybot_messages:
                        await fetch_and_parse_messages(client, target_group)  # Pass target_group, not TargetChatID

                    current_time = asyncio.get_event_loop().time()
                    if current_time >= next_message_time:
                        if send_messages and commands_with_images_gifs:
                            # Set the next message time BEFORE sending the current message
                            min_delay = int(min_time) if min_time else 1
                            max_delay = int(max_time) if max_time else 3
                            next_message_time = current_time + secrets.randbelow(max_delay - min_delay + 1) + min_delay
                            print(f"Next message will be sent in {min_delay}-{max_delay} seconds (at time {next_message_time:.1f})")
                            command = None
                            for i, cmd in enumerate(commands_with_images_gifs):
                                current_type = get_command_type(cmd)
                                if current_type != last_command_type:
                                    command = commands_with_images_gifs.pop(i)
                                    last_command_type = current_type
                                    break
                            
                            if command is None:
                                print("Could not find a different command type. Shuffling the list.")
                                random.shuffle(commands_with_images_gifs)
                                command = commands_with_images_gifs.pop(0)
                                last_command_type = get_command_type(command)
                            
                            if keep_track_of_long_comments and command in sent_long_commands:
                                print(f"\n\n!!! ATTENTION: Command '{command}' found in sent_long_commands.json. Skipping and removing all instances. !!!\n\n")
                                initial_count = len(commands_with_images_gifs)
                                commands_with_images_gifs = [cmd for cmd in commands_with_images_gifs if cmd != command]
                                removed_count = initial_count - len(commands_with_images_gifs)
                                print(f"Removed {removed_count} instance(s) of '{command}' from the command list.\n")
                            else:
                                print(f"\nSending command: {command}")
                                await send_command_with_account(client, command, TargetChatID)
                                
                                if keep_track_of_long_comments and command in formatted_long_commands:
                                    print(f"\n--- Long command '{command}' sent. Removing all instances and marking as sent. ---\n")
                                    initial_count = len(commands_with_images_gifs)
                                    commands_with_images_gifs = [cmd for cmd in commands_with_images_gifs if cmd != command]
                                    removed_count = initial_count - len(commands_with_images_gifs)
                                    print(f"Removed {removed_count} instance(s) of '{command}' from the command list.")
                                    sent_long_commands.add(command)
                                    save_sent_long_commands(sent_long_commands)
                                    print(f"Added '{command}' to sent_long_commands.json\n")

                            if not commands_with_images_gifs:
                                print("\nAll commands have been used. Repopulating command list...")
                                prepared_meme_pump_commands = [cmd.format(token=capital_token, capital_token_name=capital_token) for cmd in config['meme_pump_commands']]
                                meme_pump_count = int(len(prepared_meme_pump_commands) * meme_pump_command_count)
                                meme_pump_count = max(1, meme_pump_count)
                                sampled_meme_pump_commands = random.choices(prepared_meme_pump_commands, k=meme_pump_count)
                                commands_with_images_gifs = (sampled_meme_pump_commands + 
                                                             filters + 
                                                             ['image'] * image_count + 
                                                             ['sticker'] * sticker_count)
                                if not keep_track_of_long_comments or len(available_long_commands) > 0:
                                    commands_with_images_gifs += available_long_commands
                                random.shuffle(commands_with_images_gifs)
                                print(f"Command list repopulated with {len(commands_with_images_gifs)} commands.\n")

                else:
                    # TargetChatID is None after resolution attempt failed
                    try:
                        print(f"TargetChatID is None, re-resolving chat ID for: {target_group}")
                        TargetChatID = await resolve_target_group(client, target_group)
                        if TargetChatID is not None:
                            await wait_for_unlock(client, TargetChatID)
                            await parse_and_reply_to_messages(client, TargetChatID, user_ids)
                            if react_to_buybot_messages:
                                await fetch_and_parse_messages(client, target_group)
                            if send_messages and commands_with_images_gifs:
                                min_delay = int(min_time) if min_time else 1
                                max_delay = int(max_time) if max_time else 3
                                current_time = asyncio.get_event_loop().time()
                                next_message_time = current_time + secrets.randbelow(max_delay - min_delay + 1) + min_delay
                                command = commands_with_images_gifs.pop(0)
                                print(f"\nSending command: {command}")
                                await send_command_with_account(client, command, TargetChatID)
                    except Exception as e:
                        print(f"Error sending message: {str(e)}")

            except SessionRevoked:
                print(f"Session revoked for account {phone}. Moving to the next account.")
                continue
            except PeerIdInvalid as e:
                print(f"PeerIdInvalid error for account {phone}: {str(e)}")
                print("Clearing TargetChatID and will re-resolve on next attempt...")
                TargetChatID = None
                continue
            except sqlite3.OperationalError as e:
                print(f"SQLite error for account {phone}: {str(e)}. Deleting pyrogram_sessions and trying again.")
                os.remove(f"pyrogram_sessions/{phone}.pyrogram_sessions")
                try:
                    client = Client(f"pyrogram_sessions/{phone}", api_id=api_id, api_hash=api_hash, phone_number=phone)
                    await client.start()
                    print(f"Client Started for {phone} after recreating pyrogram_sessions")
                except SessionPasswordNeeded:
                    print(f"Two-step verification is enabled for {phone}. Please disable it or handle it in your code.")
                    continue
                except Exception as e:
                    print(f"Failed to start client for {phone} after recreating pyrogram_sessions: {str(e)}")
                    continue
            except SessionPasswordNeeded:
                print(f"Two-step verification is enabled for {phone}. Please disable it or handle it in your code.")
                continue
            except Exception as e:
                print(f"An unexpected error occurred with account {phone}: {str(e)}")
                continue
            finally:
                if client:
                    await client.stop()

        little_sleep = secrets.choice(range(1, 2))
        print(f"Sleeping for {little_sleep} seconds")
        await asyncio.sleep(little_sleep)

if __name__ == "__main__":
    asyncio.run(main())

