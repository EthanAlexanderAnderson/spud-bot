import discord, pickle
from discord.ext import commands

client = commands.Bot(command_prefix='/')       # command prefix (/)

saveFile = "save.p"

# shitpost dictionary
#dic = {'ok':'https://cdn.discordapp.com/attachments/605588158913970176/605588488112570369/image0.jpg', 'fit':'https://cdn.discordapp.com/attachments/605588158913970176/606908553906880518/fit_short.png'}
#pickle.dump(dic, open(saveFile, "wb"))

@client.event
async def on_ready():
    print('Bot is ready.')

'''
@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')

@client.event
async def on_member_remove(member):
    print(f'{member} has left a server.')
'''

@client.event
async def on_message(message):
    if message.content.startswith('/send '):
        dic = pickle.load(open(saveFile, "rb"))
        keyword = message.content.split(" ")
        msg = dic[keyword[1]]
        print(msg)
        await message.channel.send(msg)

    elif message.content.startswith('/add '):
        dic = pickle.load(open(saveFile, "rb"))
        words = message.content.split(" ")
        key = words[1]
        value = words[2]
        print(key, value)
        dic[key] = value
        print(dic)
        await message.channel.send("{} has been added".format(words[1]))
        pickle.dump(dic, open(saveFile, "wb"))

    elif message.content.startswith('/remove '):
        dic = pickle.load(open(saveFile, "rb"))
        target = message.content.split(" ")
        dic.pop(target[1])
        await message.channel.send("{} has been removed".format(target[1]))
        pickle.dump(dic, open(saveFile, "wb"))
'''
@client.event
async def on_message(message):
    if message.content.startswith('/add '):
        words = message.content.split(" ")
        key = words[1]
        value = words[2]
        print(key, value)
        dic[key] = value
        print(dic)

@client.command()
async def ok(ctx):
    await ctx.send('https://cdn.discordapp.com/attachments/605588158913970176/605588488112570369/image0.jpg')
'''
client.run('NjA1NTY5NDczMzY5MzQxOTcy.XT-aoQ.MlsyPlELpuZYmlIaLY0PQLax1cM')       #token to link code to discord bot