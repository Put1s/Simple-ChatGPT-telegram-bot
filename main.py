import openai

from pytdbot import Client, utils
from pytdbot.types import LogStreamFile, Update

client = Client(
    api_id="YOUR ID",
    api_hash="YOUR API HASH",
    database_encryption_key="DATABASE ENCRYPTION KEY",
    token="YOUR TOKEN",  # Your bot token or phone number if you want to login as user
    files_directory="BotDB",  # Path where to store TDLib files
    lib_path="LIB PATH",  # Path to TDjson shared library
    td_log=LogStreamFile("tdlib.log"),  # Set TDLib log file path
    td_verbosity=2,  # TDLib verbosity level
)

openai.api_key = "YOU OPENAI API KEY"

chats = []  # ID of chats where answers will be sent

previous_messages = dict()


def add_message(chat_id, role, message):
    if chat_id not in previous_messages:
        previous_messages[chat_id] = list()
    previous_messages[chat_id].append((role, message))
    if len(previous_messages[chat_id]) > 6:
        previous_messages[chat_id] = previous_messages[chat_id][1:]


@client.on_updateNewMessage()
async def print_message(c: Client, message: Update):
    content = message["message"]["content"]
    if content["@type"] == "messageText" and message.chat_id in chats and not message.is_self:

        if len(content["text"]["text"]) > 2000:
            await message.reply_text("К сожалению, я сейчас занят. Могу поговорить попозже.")
        else:
            await message.action("typing")
            messages = [
                {"role": "system", "content": ""},
            ]
            if message.chat_id in previous_messages:
                for [role, msg] in previous_messages[message.chat_id]:
                    messages.append({"role": role, "content": msg})
            messages.append({"role": "user", "content": content['text']['text']})
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            print(response["choices"][0])
            await message.reply_text( response["choices"][0]["message"]["content"],
                                     reply_to_message_id=message.message_id)

            add_message(message.chat_id, "user", content['text']['text'])
            add_message(message.chat_id, "assistant", response["choices"][0]["message"]["content"])
    elif content["@type"] == "messageText" and message.chat_id in chats and message.is_self:
        print(f"Added {content['text']['text']} to self messages")
        add_message(message.chat_id, "assistant", content['text']['text'])


# Run the client
client.run()
