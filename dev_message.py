import asyncio
from telethon import TelegramClient
import random
from time import sleep

# Replace these with your actual details
api_id = '23797669'
api_hash = '47822ee2b1fce119238894583ad900b2'
phone_number = '+14144063500'
target_group = 'https://t.me/SlothBucks'
folder_session = 'session/'

# The message to be sent
message_variations = [
"""🌟🦥 **Join the SlothBucks Fun: FREE TOKENS AND NFT** 🦥🌟

🚀**STEALTH LAUNCHING ON BSC JANUARY 10th**🚀

Sloth Enthusiasts! Get ready for easy-peasy missions with a cool rewards! 🚀

**HOW TO CLAIM FREE NFT** 🚀

- **Visit Our NFT Channel:** Choose and download a cute SlothBucks NFT.
- **Show Your Sloth Pride:** Set a Sloth NFT as your profile image for a week.
- **Win a Unique NFT:** After one week, claim your free NFT!

NFT CHANNEL HERE: https://t.me/+9g3caZPDpGNhYzdh

🌟 **BONUS QUEST:**

**TASK:**Complete the previous requirements AND Post 1000 messages in the group over the next seven days!

**REWARD:**Receive an airdrop of 0.1% of the total SlothBucks tokens.🦥✨

🚀🚀🚀***ULTIMATE CHALLENGE:**🚀🚀🚀

Show your unparalleled dedication to SlothBucks by inviting new users to the group.

**TASK:**
A) DM @TheSlothBucksDev for a unique invite link
B) Invite as many real crypto users as you can

**REWARD:**The top 3 winners with the most invites will each get a free airdrop of 0.5% of TOTAL TOKENS

(Invites of bots or users uninterested in crypto will result in disqualification)

**DO NOT DM ME WITH MARKETING PROPOSALS - THE CHALLENGES ALREADY IN PLACE ALLOW YOU TO EARN FREE TOKENS - I WILL NOT SEND YOU MONEY**
""",

"""🌟🦥 **Join the SlothBucks Fun: FREE TOKENS AND NFT** 🦥🌟

🚀**STEALTH LAUNCHING ON BSC JANUARY 10th**🚀

To all Sloth Aficionados! Embark on a simple yet rewarding mission! 🚀

**HOW TO CLAIM FREE NFT** 🚀

- **Visit Our NFT Channel:** Choose and download a cute SlothBucks NFT.
- **Show Your Sloth Pride:** Set a Sloth NFT as your profile image for a week.
- **Win a Unique NFT:** After one week, claim your free NFT!

NFT CHANNEL HERE: https://t.me/+9g3caZPDpGNhYzdh

🌟 **BONUS QUEST:**

Complete all the previous requirements AND
Post 1000 messages in the group over the next seven days!

Receive an airdrop of 0.1% of the total SlothBucks tokens.🦥✨

🚀🚀🚀***ULTIMATE CHALLENGE:**🚀🚀🚀

Show your unparalleled dedication to SlothBucks by inviting new users to the group.

A) DM @TheSlothBucksDev for a unique invite link
B) Invite as many real crypto users as you can

The top 3 winners with the most invites will each get a free airdrop of 0.5% of TOTAL TOKENS

(Invites of bots or users uninterested in crypto will result in disqualification)

**DO NOT DM ME WITH MARKETING PROPOSALS - THE CHALLENGES ALREADY IN PLACE ALLOW YOU TO EARN FREE TOKENS - I WILL NOT SEND YOU MONEY**

""",

"""🌟🦥 **Join the SlothBucks Fun: FREE TOKENS AND NFT** 🦥🌟

🚀**STEALTH LAUNCHING ON BSC JANUARY 10th**🚀

Sloth Fans, gear up for an easy and rewarding quest! 🚀

**HOW TO CLAIM FREE NFT** 🚀

- **Visit Our NFT Channel:** Choose and download a cute SlothBucks NFT.
- **Show Your Sloth Pride:** Set a Sloth NFT as your profile image for a week.
- **Win a Unique NFT:** After one week, claim your free NFT!

NFT CHANNEL HERE: https://t.me/+9g3caZPDpGNhYzdh

🌟 **BONUS QUEST:**

Complete all the previous requirements AND
Post 1000 messages in the group over the next seven days!

Receive an airdrop of 0.1% of the total SlothBucks tokens.🦥✨

🚀🚀🚀***ULTIMATE CHALLENGE:**🚀🚀🚀

Show your unparalleled dedication to SlothBucks by inviting new users to the group.

A) DM @TheSlothBucksDev for a unique invite link
B) Invite as many real crypto users as you can

The top 3 winners with the most invites will each get a free airdrop of 0.5% of TOTAL TOKENS

(Invites of bots or users uninterested in crypto will result in disqualification)

**DO NOT DM ME WITH MARKETING PROPOSALS - THE CHALLENGES ALREADY IN PLACE ALLOW YOU TO EARN FREE TOKENS - I WILL NOT SEND YOU MONEY**

""",

"""🌟🦥 **Join the SlothBucks Fun: FREE TOKENS AND NFT** 🦥🌟

🚀**STEALTH LAUNCHING ON BSC JANUARY 10th**🚀

**HOW TO CLAIM FREE NFT** 🚀

- **Visit Our NFT Channel:** Choose and download a cute SlothBucks NFT.
- **Show Your Sloth Pride:** Set a Sloth NFT as your profile image for a week.
- **Win a Unique NFT:** After one week, claim your free NFT!

NFT CHANNEL HERE: https://t.me/+9g3caZPDpGNhYzdh

🌟 **BONUS QUEST:**

Complete all the previous requirements AND
Post 1000 messages in the group over the next seven days!

Receive an airdrop of 0.1% of the total SlothBucks tokens.🦥✨✨

🚀🚀🚀***ULTIMATE CHALLENGE:**🚀🚀🚀

Show your unparalleled dedication to SlothBucks by inviting new users to the group.

A) DM @TheSlothBucksDev for a unique invite link
B) Invite as many real crypto users as you can

The top 3 winners with the most invites will each get a free airdrop of 0.5% of TOTAL TOKENS

(Invites of bots or users uninterested in crypto will result in disqualification)

**DO NOT DM ME WITH MARKETING PROPOSALS - THE CHALLENGES ALREADY IN PLACE ALLOW YOU TO EARN FREE TOKENS - I WILL NOT SEND YOU MONEY**

""",

"""🌟🦥 **Join the SlothBucks Fun: FREE TOKENS AND NFT** 🦥🌟

🚀**STEALTH LAUNCHING ON BSC JANUARY 10th**🚀

NFT CHANNEL HERE: https://t.me/+9g3caZPDpGNhYzdh


Attention, Sloth Fans! Prepare for a simple yet rewarding challenge! 🚀

Your Adventure Awaits:

- **Explore the NFT Channel:** Discover and download an adorable SlothBucks NFT.
- **Represent as a Sloth Ambassador:** Use a SlothBucks NFT as your profile picture for one week.
- **Claim Your Free NFT:** Stay committed and earn a unique SlothBucks NFT!

🌟 **BONUS QUEST:**

Complete all the previous requirements AND
Post 1000 messages in the group over the next seven days!

Receive an airdrop of 0.1% of the total SlothBucks tokens.🦥✨

🚀🚀🚀***ULTIMATE CHALLENGE:**🚀🚀🚀

Show your unparalleled dedication to SlothBucks by inviting new users to the group.

A) DM @TheSlothBucksDev for a unique invite link
B) Invite as many real crypto users as you can

The top 3 winners with the most invites will each get a free airdrop of 0.5% of TOTAL TOKENS

(Invites of bots or users uninterested in crypto will result in disqualification)


**DO NOT DM ME WITH MARKETING PROPOSALS - THE CHALLENGES ALREADY IN PLACE ALLOW YOU TO EARN FREE TOKENS - I WILL NOT SEND YOU MONEY**

"""


]

async def send_message_periodically():
    # Use the same session naming convention as the second script
    session_name = f"{folder_session}{phone_number}"  # Session file format

    client = TelegramClient(session_name, api_id, api_hash)

    await client.start(phone_number)
    print("Client Started")

    target_entity = await client.get_entity(target_group)

    while True:
        # Select a random message from the list
        message_to_send = random.choice(message_variations)
        message = await client.send_message(target_entity, message_to_send)
        sleep(15)
        await client.pin_message(target_entity, message)  # Pin the sent message
        print(f"Message sent and pinned to {target_group}")
        await asyncio.sleep(6000)  # Wait for 2 minutes

# Run the function
loop = asyncio.get_event_loop()
loop.run_until_complete(send_message_periodically())
