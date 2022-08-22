import discord
from discord.ext import commands
import redis
import os
import random


redis = redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True)    # loads redis server, replace "os.environ['REDIS_URL']" with your redis URL

client = commands.Bot(command_prefix='/')                                       # command prefix (/)

@client.event                                                                   # tell server when bot is ready
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_message(message):                                                  # read sent message
    if message.content.startswith('/send '):                                    # for /send
        keyword = message.content.split(" ")                                    # split message
        msg = redis.get(keyword[1])                                             # find tag in dictionary
        await message.channel.send(msg)                                         # send link connected to tag

    elif message.content.startswith('/add '):                                   # for /add
        words = message.content.split(" ")                                      # split message
        key = words[1]                                                          # define dictionary key
        value = words[2]                                                        # define dictionary value
        redis.set(str(key), str(value))                                         # add entry to dictionary
        await message.channel.send("{} has been added".format(words[1]))        # inform user the entry has been made

    elif message.content.startswith('/remove '):                                # for /remove
        target = message.content.split(" ")                                     # split message
        redis.delete(target[1])                                                 # remove entry from dictionary
        await message.channel.send("{} has been removed".format(target[1]))     # inform user the entry has been removed

    elif message.content.startswith('/list'):                                   # for /list       
        keys = redis.keys(pattern='[^&]*')                                      # defines all keys (other than dream related)
        await message.channel.send((', ').join(keys))                           # inform user of all set keys

    # dream journal game commands

    elif message.content.startswith('/dreamadd'):                               # for /dreamadd
        dreamadd = message.content.split(" ")                                   # split message
        dreamer = dreamadd[1]                                                   # define who had the dream  
        dream = (' ').join(dreamadd[2:])                                                    # define the dream contents
        i = 0
        while (redis.exists("&dream"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&dreamer"+str(i)), str(dreamer))                            # set dreamer
        redis.set(("&dream"+str(i)), str(dream))                                # set dream
        if (i > int(redis.get("&dreamcount"))):                                  # increase dream count if required
            redis.set("&dreamcount", str(i))
        await message.channel.send("Dream {} has been added".format(redis.get("&dreamcount")))
    
    elif message.content.startswith('/dreamplay'):                              # for /dreamplay
        rng = random.randint(0, int(redis.get("&dreamcount")))                   # creates random number upto dream count
        msg = redis.get("&dream"+str(rng))                                      # gets dream of random number
        await message.channel.send(msg + " ||dream#" + str(rng) + "||")       # sends dream and number for debug

    elif message.content.startswith('/dreamreveal'):                            # for /dreamreveal
        msg = redis.get("&dreamer"+str(rng))                                    # gets dreamer of random number (defined previously)
        await message.channel.send(msg + " ||dream#: " + str(rng) + "||")       # sends dreamer and number for debug

    elif message.content.startswith('/dreamcount'):                             # for /dreamcount
        msg = redis.get("&dreamcount")                                          # gets dream count
        await message.channel.send(msg)                                         # sends dream count

    elif message.content.startswith('/dreamlist'):                              # for /dreamlist       
        keys = redis.keys(pattern='&*')                                         # defines all keys (dream related)
        await message.channel.send((', ').join(keys))                           # inform user of all set keys


client.run(os.environ['BOT_TOKEN'])       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token
