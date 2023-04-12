import discord
import logging
import threading
from datetime import datetime
import asyncio

class discord_platform():
    def __init__(self, argument, messageHandler):
        self.messageHandler = messageHandler
        self.argument = argument
        td =threading.Thread(target=self.start_server).start()
    
    def start_server(self):
        intents = discord.Intents.default()
        intents.message_content = True
        client = DiscordClient(intents=intents)
        self.messageHandler.set_platform('discord', client)
        client.setup(self.argument, self.messageHandler)
        client.run(self.argument.discord_token)

class DiscordClient(discord.Client):
    def setup(self, argument, messageHandler):
        self.messageHandler = messageHandler
        self.argument = argument

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        # if message.content == 'ping':
        #     await message.channel.send('pong')

        # user_id = str(message.author.id)
        user_id = str(message.channel.id)
        receive_text = message.content
        receive_timestamp = datetime.timestamp(message.created_at)*1000
        # print(receive_timestamp)
        # logging.info('receive from %s %s',user_id,receive_text)

        reply_msg = self.messageHandler.handdle('discord',user_id, receive_text, receive_timestamp)

        # logging.info('reply to %s %s',user_id,reply_msg)
        await message.channel.send(reply_msg)

    def send_to_user(self, user_id, message):
        channel = self.get_channel(int(user_id))
        asyncio.run_coroutine_threadsafe(channel.send(message),asyncio.get_running_loop())
        # asyncio.run(channel.send(message))
        # await channel.send(message)
        # asyncio.get_event_loop().call_soon_threadsafe(channel.send(message))
    