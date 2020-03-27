import discord
from discord.ext import commands
import redis
import os

redis = redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True)    # loads redis server, replace "os.environ['REDIS_URL']" with your redis URL

client = commands.Bot(command_prefix='/')                                       # command prefix (/)


@client.event                                                                   # tell server when bot is ready
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_message(message):                                                  # read sent message
    if message.content.startswith('/send '):                                    # for /send
        keyword = message.content.split(" ")                                    # split message
        newKey = ""
        keyword = keyword[1:]
        if len(keyword) > 1:
          for i in range(len(keyword)):
            newKey = newKey + keyword[i] + " "
          newKey = str(newKey[:-1])
          key = newKey
        else:
            key = keyword[1]
        key = key.lower()
        msg = ""
        msg = redis.get(key)                                             # find tag in dictionary
        if msg is None:
            msg = "No image found."
        await message.channel.send(msg)                                         # send link connected to tag

    elif message.content.startswith('/add '):                                   # for /add
        words = message.content.split(" ")                                      # split message
        key = words[1:-1]                                                       # define dictionary key
        value = words[-1]                                                       # define dictionary value
        if len(key) > 1:
            newKey = ""
            for i in range(len(key)):
                newKey = newKey + key[i] + " "
            newKey = str(newKey[:-1])
            key = newKey
        key = str(key)
        key = key.lower()
        redis.set(str(key), str(value))                                         # add entry to dictionary
        await message.channel.send("{} has been added".format(key))        # inform user the entry has been made

    elif message.content.startswith('/remove '):                                # for /remove
        target = message.content.split(" ")                                     # split message
        redis.delete(target[1])                                                 # remove entry from dictionary
        await message.channel.send("{} has been removed".format(target[1]))     # inform user the entry has been removed

    elif message.content.startswith('/list'):                                   # for /list
        allKeys = redis.keys('*')                                               # defines all keys
        await message.channel.send((', ').join(allKeys))                        # inform user of all set keys

client.run(os.environ['BOT_TOKEN'])       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token
