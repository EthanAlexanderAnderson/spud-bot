import discord, pickle
from discord.ext import commands

client = commands.Bot(command_prefix='/')       # command prefix (/)

saveFile = "save.p"     # file where dictionary (tags & links) are stored 

@client.event                       # tell server when bot is ready
async def on_ready():
    print('Bot is ready.')

@client.event
async def on_message(message):      # read sent message
    if message.content.startswith('/send '):        # for /send
        dic = pickle.load(open(saveFile, "rb"))     # load dictionary from file
        keyword = message.content.split(" ")        # split message
        msg = dic[keyword[1]]                       # find tag in dictionary
        await message.channel.send(msg)             # send link connected to tag

    elif message.content.startswith('/add '):       # for /add
        dic = pickle.load(open(saveFile, "rb"))     # load dictionary from file
        words = message.content.split(" ")          # split message
        key = words[1]                              # define dictionary key
        value = words[2]                            # define dictionary value
        dic[key] = value                            # add entry to dictionary 
        await message.channel.send("{} has been added".format(words[1]))        # inform user the entry has been made
        pickle.dump(dic, open(saveFile, "wb"))      # update dictionary file

    elif message.content.startswith('/remove '):    # for /remove
        dic = pickle.load(open(saveFile, "rb"))     # load dictionary from file
        target = message.content.split(" ")         # split message
        dic.pop(target[1])                          # remove entry from dictionary
        await message.channel.send("{} has been removed".format(target[1]))     # inform user the entry has been removed
        pickle.dump(dic, open(saveFile, "wb"))      # update dictionary file

client.run('NjA1NTY5NDczMzY5MzQxOTcy.XUTakw.tLN4EXL_TLm0FKo1Nq7YTPKoS3I')       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token
