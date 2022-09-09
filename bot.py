import discord
from discord.ext import commands
import redis
import os
import random

# -- global variables --
redis = redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True)    # loads redis server, replace "os.environ['REDIS_URL']" with your redis URL

client = commands.Bot(command_prefix='/', intents=discord.Intents.all())        # command prefix (/)

names = ["Ethan", "Ham", "Anderson", "Oobie", "Oob", "Scoobie", "Larose", "Nathan", "Nash", "Nate", "Nashton", "Skrimp", "Ashton", "Eric", "Ric", "Rick", "Mitch", "Mitchell", "Maxwel", "Maximillion", "Max", "Maxwell", "Mac", "Macs", "MTG", "MT", "Cole", "Devon", "Devo", "Deevi", "Shmev", "Eddie", "Edmund", "Ed", "Adam", "Chad", "Chadam", "Dylan", "Teddy", " Jack", "Jac", "Jak", "Zach", "Zack", "Zac", "Zak", "Zachary"]
buffer = []

# -- Bot Functionality --
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

    # -- dream journal game commands --

    elif message.content.startswith('/dreamadd') or message.content.startswith('/da'):                            # for /dreamreveal
        dreamadd = message.content.split(" ")                                   # split message
        dreamer = dreamadd[1]                                                   # define who had the dream  
        dream = (' ').join(dreamadd[2:])                                        # define the dream contents
        i = 0
        while (redis.exists("&dream"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&dreamer"+str(i)), str(dreamer))                            # set dreamer
        redis.set(("&dream"+str(i)), str(dream))                                # set dream
        if (i > int(redis.get("&dreamcount"))):                                 # increase dream count if required
            redis.set("&dreamcount", str(i))
        await message.channel.send("Dream {} has been added. Dreamer: {}".format(redis.get("&dreamcount"),str(dreamer)))
    
    elif message.content.startswith('/dreamplay') or message.content.startswith('/dp'):                            # for /dreamreveal
        # initialize variables
        censor = False
        fake = False
        msg = message.content.split(" ")
        dreamCount = int(redis.get("&dreamcount"))
        fakeCount = int(redis.get("&fakecount"))
        # check for flags and set variables
        if (len(msg) > 1):
            if ('C' in msg or 'c' in msg):
                censor = True
            if ('F' in msg or 'f' in msg):
                fake = True

        # generate random number for dream (buffer is used to avoid repeats)
        rng = random.randint(0, dreamCount) if fake == False else random.randint(0, dreamCount + fakeCount )               
        global buffer
        while rng in buffer:
            rng = random.randint(0, dreamCount) if fake == False else random.randint(0, dreamCount + fakeCount )
        buffer.append(rng)
        if len(buffer) > 50:
            del buffer[0]

        # get dream (or fake) from database
        if rng <= dreamCount:
            msg = redis.get("&dream"+str(rng))   
            redis.set("&dreamtemp", redis.get("&dreamer"+str(rng)))
        else:
            rng -= dreamCount
            msg = redis.get("&fake"+str(rng))
            redis.set("&dreamtemp", redis.get("&faker"+str(rng)))

        # if censor flag is true, censor names
        if censor:
            censored = msg.split(" ")
            # nested for loop to search for names
            for i in range(len(censored)):
                for j in range(len(names)):
                    if censored[i].lower() == names[j].lower():
                        censored[i] = "###"
                    elif censored[i].lower() == (names[j].lower()+"’s"):
                        censored[i] = "###’s"
                    elif censored[i].lower() == (names[j].lower()+"s"):
                        censored[i] = "###s"
                    elif censored[i].lower() == (names[j].lower()+","):
                        censored[i] = "###,"
                    elif censored[i].lower() == (names[j].lower()+"."):
                        censored[i] = "###."
            msg = (" ").join(censored)

        await message.channel.send(msg + " ||#" + str(rng) + "||")             # sends dream and number for debug

    elif message.content.startswith('/dreamreveal') or message.content.endswith('/dr'):                            # for /dreamreveal
        msg = redis.get("&dreamtemp")                                           # gets dreamer of random number (defined previously)
        await message.channel.send(msg)                                         # sends dreamer and number for debug

    elif message.content.startswith('/dreamcount') or message.content.startswith('/dc'):                            # for /dreamreveal
        msg = redis.get("&dreamcount")                                          # gets dream count
        await message.channel.send(msg)                                         # sends dream count

    elif message.content.startswith('/dreamsend') or message.content.startswith('/ds'):
        msg = message.content.split(" ")
        num = msg[1]
        msg = redis.get("&dream" + num) + " ||" + redis.get("&dreamer" + num) + "||"
        await message.channel.send(msg)

    elif message.content.startswith('/dreamname') or message.content.startswith('/dn'):                            # for /dreamreveal
        total = 0
        msg = message.content.split(" ")
        name = msg[1]
        count = int(redis.get("&dreamcount"))
        list = []
        for i in range(count):
            if (redis.get("&dreamer" + str(i)) == name):
                list.append(str(i))
                total+=1
        await message.channel.send("Count: " + str(total) + ". Dream IDs: " + (', ').join(list))                           # inform user of all set keys

    # Fake functions

    elif message.content.startswith('/dreamfake') or message.content.startswith('/df'):                          # for /dreamfake
        dreamfake = message.content.split(" ")                                   # split message
        faker = dreamfake[1]                                                   # define who had the dream  
        fake = (' ').join(dreamfake[2:])                                        # define the dream contents
        i = 0
        while (redis.exists("&fake"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&faker"+str(i)), ("Fake by " + str(faker)))                            # set dreamer
        redis.set(("&fake"+str(i)), str(fake))                                # set dream
        if (i > int(redis.get("&fakecount"))):                                 # increase dream count if required
            redis.set("&fakecount", str(i))
        await message.channel.send("Fake dream {} has been added. Fake writer: {}".format(redis.get("&fakecount"),str(faker)))
    
    #debug
    elif message.content.startswith('/dreamdebug'):
        await message.channel.send("Buffer Length: " + str(len(buffer)))
        await message.channel.send("Buffer Content: " + (', ').map(str, buffer))

client.run(os.environ['BOT_TOKEN'])       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token
