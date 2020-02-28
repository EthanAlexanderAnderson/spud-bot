import discord
import json
from discord.ext import commands
import os
import redis

redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
#redis.set("test", "hell yes")
#result = redis.get("test").decode('utf-8')
#print(result)
#print("or nah")
#redis.echo("please help me")

client = commands.Bot(command_prefix='/')       # command prefix (/)

     # file where dictionary (tags & links) are stored

while True:
    try:
        with open("myson.json", "r") as read_file:
            dic = json.load(read_file)
        break
    except json.decoder.JSONDecodeError:
        dic={}
        with open("myson.json", "w") as write_file:
            dic = json.dump(dic, write_file)
'''
dic={}
with open("myson.json", "w") as write_file:
    dic = json.dump(dic, write_file)
'''

@client.event                       # tell server when bot is ready
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_message(message):      # read sent message
    global write_file, read_file, dic
    if message.content.startswith('/send '):        # for /send
        keyword = message.content.split(" ")        # split message
        msg = redis.get(keyword[1])     # find tag in dictionary
        await message.channel.send(msg)             # send link connected to tag

    elif message.content.startswith('/add '):       # for /add
        words = message.content.split(" ")          # split message
        key = words[1]                              # define dictionary key
        value = words[2]                            # define dictionary value
        redis.set(str(key), str(value))                            # add entry to dictionary
        await message.channel.send("{} has been added".format(words[1]))        # inform user the entry has been made


    elif message.content.startswith('/remove '):    # for /remove
        target = message.content.split(" ")         # split message
        redis.delete(target[1])                          # remove entry from dictionary
        await message.channel.send("{} has been removed".format(target[1]))     # inform user the entry has been removed

    elif message.content.startswith('/list'):
        allKeys = redis.keys('*')
        await message.channel.send((', ').join(allKeys))

client.run(BOT_TOKEN)       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token


