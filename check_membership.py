import sys
import os
import json
import logging
from datetime import datetime
import asyncio
from telethon import TelegramClient, errors

# Add this code to suppress INFO-level messages from Telethon
logging.getLogger('telethon').setLevel(logging.WARNING)

async def check_membership(phone_number, api_id, api_hash, group_target, member_count, non_member_count):
    session_path = os.path.join('telethon_sessions', phone_number)
    client = TelegramClient(session_path, api_id, api_hash)

    try:
        await client.start()
    except errors.PhoneNumberInvalidError:
        logging.error(f'Invalid phone number: {phone_number}')
        return

    if await client.is_user_authorized():
        try:
            group = await client.get_entity(group_target)
            # Try to fetch some messages from the group. If successful, user is a member.
            await client.get_messages(group, limit=1)
            print(f'{phone_number} is a member of the join group. {group_target} \n')
            member_count += 1
        except errors.ChannelPrivateError:
            print(f'{phone_number} is not a member of the target group.\n')
            non_member_count += 1
        except Exception as e:
            logging.error(f'Error checking membership for {phone_number}: {str(e)}')
        await client.disconnect()
    else:
        logging.info(f'{phone_number} login fail')

    return member_count, non_member_count

async def main():
    # Read configuration from command line argument or default to config.json
    config_file = sys.argv[1] if len(sys.argv) > 1 else 'config.json'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.loads(f.read())

    api_id = int(config['api_id'])
    api_hash = config['api_hash']
    group_target = config['join_group']
    accounts = config['accounts']

    start_time = datetime.now()
    member_count = 0
    non_member_count = 0

    for phone_number in accounts:
        member_count, non_member_count = await check_membership(phone_number, api_id, api_hash, group_target, member_count, non_member_count)
        await asyncio.sleep(1)  # Wait for 1 second between checks

    end_time = datetime.now()
    logging.info("Total time: " + str(end_time - start_time))

    print(f'Total members in the target group: {member_count}')
    print(f'Total non-members in the target group: {non_member_count}')
    input()
if __name__ == '__main__':
    asyncio.run(main())
