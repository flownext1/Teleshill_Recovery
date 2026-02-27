from telethon import TelegramClient, types, utils
import asyncio
import json
import random
import os
from time import sleep
from itertools import cycle
import re
from telethon import functions

# Load the configuration
with open('configCopypasta.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# Read copypastas from the file
with open('copypasta.json', 'r', encoding='utf-8') as f:
    copypasta_data = json.load(f)
    copypastas = copypasta_data['copypastas']

copypasta_iter = cycle(copypastas)

async def send_copypasta(client, target_entity, copypasta):
    # Replace {token_name} with the actual token name
    formatted_copypasta = copypasta.format(token_name=config['token_name'])

    # Split the formatted copypasta into sentences
    sentences = re.split(r'(?<=[.!?]) +', formatted_copypasta)
    
    # Group sentences into parts of up to max_length characters
    max_length = 400
    copypasta_parts = []
    part = ""
    for sentence in sentences:
        if len(part + sentence) <= max_length:
            part += sentence + " "
        else:
            copypasta_parts.append(part)
            part = sentence + " "
    if part:  # Add the last part if not empty
        copypasta_parts.append(part)

    # Send each part with a delay and typing action
    for part in copypasta_parts:
        # Notify the chat that we're 'typing' a message
        await client(functions.messages.SetTypingRequest(
            peer=target_entity,
            action=types.SendMessageTypingAction()
        ))
        typingtime = random.randint(20,30)
        await asyncio.sleep(typingtime)  # Typing delay
        await client.send_message(target_entity, part.strip())
        print(f"Part of copypasta sent to {target_group}")
        await asyncio.sleep(4)  # Delay between parts, adjust as needed

speed = 1
api_id = config['api_id']
api_hash = config['api_hash']
accounts = config['accounts']
target_group = config['group_target']
token_name = config['token_name']
folder_session = 'session/'  # Directory for storing session files

async def main():
    while True:
        for phone in accounts:
            session_name = f"{folder_session}{phone}"
            client = TelegramClient(session_name, api_id, api_hash)
            
            async def custom_phone():
                print(f"[CODE REQUESTED] Enter code for {phone}: ")
                return input(f"[CODE REQUESTED] Enter code for {phone}: ")
            
            await client.start(phone=phone, code_callback=custom_phone)
            print(f"Client Created for {phone}")

            target_entity = await client.get_entity(target_group)
            copypasta = next(copypasta_iter)
            await send_copypasta(client, target_entity, copypasta)
            await client.disconnect()

            #sleep_time = random.randint(1, speed)
            #print(f"Sleeping for {sleep_time} seconds")
            #await asyncio.sleep(sleep_time)

asyncio.run(main())
