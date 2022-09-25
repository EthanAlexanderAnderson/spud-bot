from pickle import TRUE
import discord
from discord.ext import commands
import redis
import os
import random
from collections import defaultdict

# -- global variables --
redis = redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True)    # loads redis server, replace "os.environ['REDIS_URL']" with your redis URL
client = commands.Bot(command_prefix='/', intents=discord.Intents.all())        # command prefix (/)

# global variables for dream journal game
# TODO make lists of aliases for each person so that you can guess any alias (or abbreviation like 'N' for Nathana)
# TODO make all multi-line sends into single lines to eliminate cooldown issue
# TODO bonus point system
names = ["Ethan", "Ham", "Anderson", "Oobie", "Oob", "Scoobie", "Larose", "Nathan", "Nash", "Nate", "Nashton", "Skrimp", "Ashton", "Eric", "Ric", "Rick", "Mitch", "Mitchell", "Maxwel", "Maximillion", "Max", "Maxwell", "Mac", "Macs", "MTG", "MT", "Cole", "Devon", "Devo", "Deevi", "Shmev", "Eddie", "Edmund", "Ed", "Adam", "Chad", "Chadam", "Dylan", "Teddy", "Jack", "Jac", "Jak", "Zach", "Zack", "Zac", "Zak", "Zachary", "AI", "Fake"]
answer = ""
buffer = []
guesses = 0
guessed = []
scores = defaultdict(int)
players = 0
channelplaying = 0
#bonus variables
streaks = defaultdict(int)
streaksBroken = 0
correct = []
bonus = False

# -- Bot Functionality --
@client.event                                                                   # tell console when bot is ready
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_message(message):                                                  # read sent message
    global answer, buffer, guesses, guessed, scores, players, channelplaying, streaks, streaksBroken, correct, bonus

    if message.content.startswith('/send '):                                    # for /send
        keyword = message.content.split(" ")                                    # split incoming message
        msg = redis.get(keyword[1])                                             # find tag in dictionary
        await message.channel.send(msg)                                         # send link connected to tag

    elif message.content.startswith('/add '):                                   # for /add
        words = message.content.split(" ")                                      # split incoming message
        key = words[1]                                                          # define dictionary key
        value = words[2]                                                        # define dictionary value
        redis.set(str(key), str(value))                                         # add entry to dictionary
        await message.channel.send("{} has been added".format(words[1]))        # inform user the entry has been made

    elif message.content.startswith('/remove '):                                # for /remove
        target = message.content.split(" ")                                     # split incoming message
        redis.delete(target[1])                                                 # remove entry from dictionary
        await message.channel.send("{} has been removed".format(target[1]))     # inform user the entry has been removed

    elif message.content.startswith('/list'):                                   # for /list       
        keys = redis.keys(pattern='[^&]*')                                      # defines all keys (other than dream related)
        await message.channel.send((', ').join(keys))                           # inform user of all set keys

    # -- Dream Journal Game Commands --

    elif message.content.startswith('/dreamadd') or message.content.startswith('/da'):
        # Input processing and validation
        dreamadd = message.content.split(" ")                                   # split incoming message
        if len(dreamadd) < 3:
            await message.channel.send("Error: Missing required inputs")
        dreamer = dreamadd[1].capitalize()                                      # define who had the dream  
        dream = (' ').join(dreamadd[2:])                                        # define the dream contents
        if dreamer not in names:                                                # input validation
            await message.channel.send("Error: Invalid dreamer name")           # throw error to user
            return
        i = 0
        while (redis.exists("&dream"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&dreamer"+str(i)), str(dreamer))                            # set dreamer
        redis.set(("&dream"+str(i)), str(dream))                                # set dream
        if (i > int(redis.get("&dreamcount"))):                                 # increase dream count if required
            redis.set("&dreamcount", str(i))
        await message.channel.send("Dream {} has been added. Dreamer: {}".format(redis.get("&dreamcount"),str(dreamer)))
    
    elif message.content.startswith('/dreamplay') or message.content.startswith('/dp'):
        # initialize variables
        guesses = 0
        guessed = []
        censor = False
        fake = False
        AI = False
        bonus = False
        msg = message.content.split(" ")
        dreamCount = int(redis.get("&dreamcount"))
        fakeCount = int(redis.get("&fakecount"))
        AICount = int(redis.get("&AIcount"))
        # check for flags and set variables
        if (len(msg) > 1):
            if msg[1].isdigit():
                players = int(msg[1])
                channelplaying = message.channel.id
            if ('C' in msg or 'c' in msg):
                censor = True
            if ('F' in msg or 'f' in msg):
                fake = True
            if ('AI' in msg or 'ai' in msg or 'Ai' in msg):
                AI = True
            if ('B' in msg or 'b' in msg):
                bonus = True

        # generate random number for dream (buffer is used to avoid repeats)
        maxCount = dreamCount
        if fake == True:
            maxCount += fakeCount
        if AI == True:
            maxCount += AICount
        rng = random.randint(0, maxCount)          
        while rng in buffer:
            rng = random.randint(0, maxCount)
        buffer.append(rng)
        if len(buffer) > 50:
            del buffer[0]

        # get dream from database
        if rng <= dreamCount:
            msg = redis.get("&dream"+str(rng))
            answer = redis.get("&dreamer"+str(rng))
            #redis.set("&dreamtemp", redis.get("&dreamer"+str(rng)))
        # fake mode
        elif rng > dreamCount and fake and not AI:
            rng -= dreamCount
            msg = redis.get("&fake"+str(rng))
            answer = "Fake"
            #redis.set("&dreamtemp", "Fake")
        # AI mode
        elif rng > dreamCount and AI and not fake:
            rng -= dreamCount
            msg = redis.get("&AI"+str(rng))
            answer = "AI"
            #redis.set("&dreamtemp", "AI")
        #both mode
        elif rng > dreamCount and AI and fake:
            rng -= dreamCount
            if rng <= fakeCount:
                msg = redis.get("&fake"+str(rng))
                answer = "Fake"
                #redis.set("&dreamtemp", "Fake")
            else:
                rng -= fakeCount
                msg = redis.get("&AI"+str(rng))
                answer = "AI"
                #redis.set("&dreamtemp", "AI")

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
                    elif censored[i].lower() == (names[j].lower()+"'s"):
                        censored[i] = "###'s"
                    elif censored[i].lower() == (names[j].lower()+"s"):
                        censored[i] = "###s"
                    elif censored[i].lower() == (names[j].lower()+","):
                        censored[i] = "###,"
                    elif censored[i].lower() == (names[j].lower()+"."):
                        censored[i] = "###."
                    elif censored[i].lower() == (names[j].lower()+")"):
                        censored[i] = "###)"
                    elif censored[i].lower() == ("("+names[j].lower()):
                        censored[i] = "(###"
            msg = (" ").join(censored)

        await message.channel.send(msg + " ||#" + str(rng) + "||")             # sends dream and number for debug

    elif message.content.startswith('/dreamreveal') or message.content.endswith('/dr'):                            # for /dreamreveal
        # cheat prevention
        if guesses < players:
            await message.channel.send("This commmand is disabled while dreamplay is active")
            return
        
        msg = answer
        #msg = redis.get("&dreamtemp")                                           # gets dreamer of random number (defined previously)
        await message.channel.send(msg)                                         # sends dreamer and number for debug

    elif message.content.startswith('/dreamcount') or message.content.startswith('/dc'):                            # for /dreamreveal
        await message.channel.send("Dreams: " + redis.get("&dreamcount"))                                         # sends dream count
        await message.channel.send("Fake dreams: " + redis.get("&fakecount"))                                         # sends dream count
        await message.channel.send("AI generated dreams: " + redis.get("&AIcount"))

    elif message.content.startswith('/dreamsend') or message.content.startswith('/ds'):
        # cheat prevention
        if guesses < players:
            await message.channel.send("This commmand is disabled while dreamplay is active")
            return
        
        msg = message.content.split(" ")
        num = msg[1]
        if len(msg) > 2:
            if msg[2].upper() == "AI":
                msg = redis.get("&AI" + num)
            elif msg[2].upper() == "FAKE":
                msg = redis.get("&fake" + num)
        else:
            msg = redis.get("&dream" + num) + " ||" + redis.get("&dreamer" + num) + "||"
        await message.channel.send(msg)

    elif message.content.startswith('/dreamname') or message.content.startswith('/dn'):                            # for /dreamreveal
        msg = message.content.split(" ")
        total = 0
        count = int(redis.get("&dreamcount"))
        list = []
        dict = defaultdict(int)

        if (len(msg) > 1):       # if name is provided
            name = msg[1]
            if name not in names:                                                # input validation
                await message.channel.send("Error: Invalid name")           # throw error to user
                return

            for i in range(count):
                if (redis.get("&dreamer" + str(i)) == name):
                    list.append(str(i))
                    total+=1
            if total > 0:
                await message.channel.send("Count: " + str(total) + ". Dream IDs: " + (', ').join(list))                           # inform user of all set keys
            else:
                await message.channel.send("Error: No dreams under the name " + name)
        else:       # if no name
            for i in range(count):
                dict[redis.get("&dreamer" + str(i))] += 1
            await message.channel.send("Count per name: ")
            msgout = ""
            for key in dict:
                msgout += key + ": " + str(dict[key]) + "\n"
            await message.channel.send(msgout)


    # Resets all global variables
    elif message.content.startswith('/dreamreset'):
        buffer = []
        guesses = 0
        guessed = []
        scores = defaultdict(int)
        players = 0
        channelplaying = 0
        await message.channel.send("Scores reset.")

    # skip feature, also doubles as insurance encase a user puts too high of a playercount
    elif message.content.startswith('/dreamskip'):
        guesses = 0
        guessed = []
        players = 0 
        await message.channel.send("Dream skipped.")

    # Fake functions

    elif message.content.startswith('/dreamfake') or message.content.startswith('/df'):                          # for /dreamfake
        dreamfake = message.content.split(" ")                                   # split message
        if len(dreamfake) < 3:
            await message.channel.send("Error: Dream must be more than one word.")
        fake = (' ').join(dreamfake[1:])                                        # define the dream contents
        i = 0
        while (redis.exists("&fake"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&fake"+str(i)), str(fake))                                # set dream
        if (i > int(redis.get("&fakecount"))):                                 # increase dream count if required
            redis.set("&fakecount", str(i))
        await message.channel.send("Fake dream {} has been added.".format(redis.get("&fakecount")))
    

    # AI functions (same concept as fakes, just seperated for gamemode customizability)

    elif message.content.startswith('/dreamAI') or message.content.startswith('/dAI'):
        dreamAI = message.content.split(" ")                                   # split message
        if len(dreamAI) < 4:
            await message.channel.send("Error: AI dreams must be 3 or more words in length.")
        dreamAI = (' ').join(dreamAI[1:])                                        # define the dream contents
        i = 0
        while (redis.exists("&AI"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&AI"+str(i)), str(dreamAI))                                # set dream
        if (i > int(redis.get("&AIcount"))):                                 # increase dream count if required
            redis.set("&AIcount", str(i))
        await message.channel.send("AI dream {} has been added.".format(redis.get("&AIcount")))

    elif message.content.startswith('/dreamundo'):
        msg = message.content.split(" ")
        if len(msg) < 3 or not msg[1].isdigit():
            await message.channel.send("Error: Missing required inputs.")
            await message.channel.send("Please use this format: `/dreamundo [dream number] [dreamer name]`")
            return
        if int(msg[1]) != int(redis.get("&dreamcount")):
            await message.channel.send("Error: Only the most recently added dream can be undone.")
            await message.channel.send("Please use this format: `/dreamundo [dream number] [dreamer name]`")
            return
        if msg[2] not in names:
            await message.channel.send("Error: Invalid name provided.")
            await message.channel.send("Please use this format: `/dreamundo [dream number] [dreamer name]`")
            return
        if redis.get("&dreamer"+redis.get("&dreamcount")) == msg[2]:    # final layer of protection
            redis.delete("&dream"+redis.get("&dreamcount"))
            redis.delete("&dreamer"+redis.get("&dreamcount"))
            await message.channel.send("Dream {} by {} has been undone.".format(msg[1], msg[2]))     # inform user the entry has been removed
            # decrease dreamcount
            redis.set("&dreamcount", str(int(redis.get("&dreamcount")) - 1))

    #debug
    elif message.content.startswith('/dreamdebug'):
        await message.channel.send("Buffer Length: " + str(len(buffer)) + "\n" + "Buffer Content: " + (', ').join(map(str, buffer)))
        await message.channel.send("Guesses: " + str(guesses) + "\n" + "Guessed: " + str(guessed))
        await message.channel.send("Scores: ")
        for player, score in scores.items():
            await message.channel.send("<@{}>: {}".format(player, score))
        await message.channel.send("Players: " + str(players) + "\n" + "Channel Playing: <#" + str(channelplaying) + ">")


    # for scoring (must be at the bottom to not interfere with other commands)
    elif guesses < players and message.author.id != client.user.id:

        #dreamTemp = redis.get("&dreamtemp").split(" ")
        guess = message.content

        # prevent double guess
        if message.author.id in guessed:
            return

        if (guess.capitalize() in names or guess.upper() in names) and guess.lower() == answer.lower():
            scores[message.author.id] += 1
            streaks[message.author.id] += 1
            correct.append(message.author.id)
        else:
            if streaks[message.author.id] >= 5:
                streaksBroken += 1
            streaks[message.author.id] = 0

        guessed.append(message.author.id)
        guesses += 1

        if guesses >= players:
            channel = client.get_channel(channelplaying)

            # evaluate bonuses
            if bonus:
                bonusMsg = "BONUSES:\n"
                streakMsg = ""
                breakerMsg = ""
                # underdog bonus
                # --- sort scores - https://stackoverflow.com/questions/52141785/sort-dict-by-values-in-python-3-6
                scores = {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
                keys = scores.keys()
                if keys[-1] in correct and keys[0] not in correct and (scores[0] - scores[-1] > 0):
                    scores[keys[-1]] += 1
                    bonusMsg += "Underdog: <@{}>\n".format(keys[-1])
                # streak bonus
                for player, streak in streaks.items():
                    if streak >= 5:
                        scores[player] += 1
                        streakMsg += "<@{}>, ".format(player)
                    bonusMsg += ("Streaks: " + streakMsg + "\n")
                # Lone wolf bonus
                if len(correct) == 1:
                    scores[correct[0]] += 1
                    bonusMsg += "Lone Wolf: <@{}>\n".format(correct[0])
                # Early bird bonus
                if guessed[0] in correct and guessed[-1] not in correct:
                    scores[guessed[0]] += 1
                    bonusMsg += "Early Bird: <@{}>\n".format(guessed[0])
                # streak broken bonus
                if streaksBroken > 0:
                    for player in correct:
                        scores[player] += 1
                        breakerMsg += "<@{}>, ".format(player)
                    bonusMsg += ("Streak Breakers: " + breakerMsg + "\n")

            # auto reveal and show scores
            scores = {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
            msg = answer
            #msg = redis.get("&dreamtemp")
            await channel.send("Answer: " + msg + "\n" + "Scores: ")    
            for player, score in scores.items():
                await channel.send("<@{}>: {}".format(player, score))

            # bonus messages
            if bonus:
                await channel.send(bonusMsg)

            # reset
            players = 0
            guessed = []
            streaksBroken = 0
            correct = []
            bonusMsg = ""
            streakMsg = ""
            breakerMsg = ""


client.run(os.environ['BOT_TOKEN'])       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token