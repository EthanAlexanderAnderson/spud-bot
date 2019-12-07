import discord
import json
from discord.ext import commands

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
        with open("myson.json", "r") as read_file:
            dic = json.load(read_file)              # load dictionary from file ---
        keyword = message.content.split(" ")        # split message
        msg = dic[keyword[1]]                       # find tag in dictionary
        await message.channel.send(msg)             # send link connected to tag

    elif message.content.startswith('/add '):       # for /add
        with open("myson.json", "r") as read_file:
            dic = json.load(read_file)              # load dictionary from file
        words = message.content.split(" ")          # split message
        key = words[1]                              # define dictionary key
        value = words[2]                            # define dictionary value
        dic[key] = value                            # add entry to dictionary
        await message.channel.send("{} has been added".format(words[1]))        # inform user the entry has been made
        #pickle.dump(dic, open(saveFile, "wb"))      # update dictionary file
        with open("myson.json", "w") as write_file:
            dic = json.dump(dic, write_file)


    elif message.content.startswith('/remove '):    # for /remove
        with open("myson.json", "r") as read_file:
            dic = json.load(read_file)       # load dictionary from file
        target = message.content.split(" ")         # split message
        dic.pop(target[1])                          # remove entry from dictionary
        await message.channel.send("{} has been removed".format(target[1]))     # inform user the entry has been removed
        with open("myson.json", "w") as write_file:
            dic = json.dump(dic, write_file)     # update dictionary file

client.run('BOT_TOKEN')       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token


