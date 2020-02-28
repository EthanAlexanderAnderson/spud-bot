from discord.ext import commands
import redis

redis = redis.Redis.from_url('redis://h:pd461d2ca0afbb0e93ddfcda006691526b53a83f255f1420c145b5a39eec47ba9@ec2-34-203-164-221.compute-1.amazonaws.com:13299', decode_responses=True)

client = commands.Bot(command_prefix='/')       # command prefix (/)


@client.event                       # tell server when bot is ready
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_message(message):      # read sent message
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


