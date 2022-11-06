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
# TODO make all multi-line sends into single lines to eliminate cooldown" issue
namesStrict = ["Ethan", "Nathan", "Cole", "Max", "Devon", "Oobie", "Eric", "Dylan", "Adam", "Mitch", "Jack", "Zach", "Devo", "Eddie"]
names = ["Ethan", "Ham", "Anderson", "Oobie", "Oob", "Scoobie", "Larose", "Nathan", "Nash", "Nate", "Nashton", "Skrimp", "Ashton", "Eric", "Ric", "Rick", "Mitch", "Mitchell", "Maxwel", "Maximillion", "Max", "Maxwell", "Mac", "Macs", "MTG", "MT", "Cole", "Devon", "Devo", "Deevi", "Shmev", "Eddie", "Edmund", "Ed", "Adam", "Chad", "Chadam", "Dylan", "Teddy", "Jack", "Jac", "Jak", "Zach", "Zack", "Zac", "Zak", "Zachary", "AI", "Fake"]
aliases = [["Ethan", "Anderson", "Ethan Anderson", "Ethan A", "Ham", "Hammie", "Hammy", "eman", "eman826", "Et", "Eth", "Etha", "Ander", "EA"], ["Oobie", "Stew", "Oobie Stew", "Oob", "Scoobie", "Beta", "Weeb", "Larose", "Ethan Larose", "Ethan L", "OS", "OB", "O"], ["Nathan", "Asthon", "Nathan Ashton", "Nathan A", "Nash", "Nate", "Nashton", "Skrimp", "Big Skrimp", "BS", "NA", "N"], ["Eric", "Linguine", "Eric L", "Ric", "Rick", "EL"], ["Mitch", "Mitchell", "MS"], ["Max", "Max K", "Maxwell", "Maxwel", "Maximillion", "Mac", "Macs", "MTG", "MT", "MK"], ["Cole", "Coal", "Cole H", "Justin", "Pokerstars", "CH", "C"], ["Devon", "Devon C", "Dev", "DC"], ["Devo", "Devo S", "Devon S", "Deevi", "Shmev", "DS"], ["Eddie", "Edmund", "Ed", "EB"], ["Adam", "Adam G", "Chad", "Chadam", "Graf", "AG", "A"], ["Dylan", "Dylan C", "Teddy", "Ted", "Cam", "LZ", "T"], ["Jack", "Jack M", "Jack Mac", "Jac", "Jak", "JM", "J"], ["Zach", "Zach R", "Zack", "Zac", "Zak", "Zachary", "ZR", "Z"], ["AI", "Bot", "Chester"], ["Fake", "Fak", "Fa", "F"]]
emojiNums = ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
answer = ""
buffer = []
guessCount = 0
guessCountUnique = 0
namesGuessed = []
guessed = []
scores = defaultdict(int)
scoresPrev = defaultdict(int)
players = 0
channelplaying = 0
# flags
censor = fake = AI = False
# bonus variables
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
    global answer, buffer, guessCount, guessCountUnique, namesGuessed, guessed, scores, scoresPrev, scoresPrevKeys, players, channelplaying, streaks, streaksBroken, correct, bonus
    global censor, fake, AI

    if message.content.startswith('/send '):                                    # for /send
        keyword = message.content.split(" ")                                    # split incoming message
        msg = redis.get((' ').join(keyword[1:]))                                             # find tag in dictionary
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
            return
        dreamer = dreamadd[1].capitalize()                                      # define who had the dream  
        dream = (' ').join(dreamadd[2:])                                        # define the dream contents
        if dreamer not in namesStrict:                                          # input validation
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
        guessCount = 0
        guessed = []
        msg = message.content.split(" ")
        dreamCount = int(redis.get("&dreamcount"))
        fakeCount = int(redis.get("&fakecount"))
        AICount = int(redis.get("&AIcount"))
        # check for flags and set variables
        if (len(msg) > 1):
            if ('N' not in msg and 'n' not in msg): # dont reset flags if /dp n is used. n meaning next round
                censor = False
                fake = False
                AI = False
                bonus = False
                players = 0
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
        if len(buffer) > 100:
            del buffer[0]

        # get dream from database
        if rng <= dreamCount:
            msg = redis.get("&dream"+str(rng))
            answer = redis.get("&dreamer"+str(rng))
        # fake mode
        elif rng > dreamCount and fake and not AI:
            rng -= dreamCount
            msg = redis.get("&fake"+str(rng))
            answer = "Fake"
        # AI mode
        elif rng > dreamCount and AI and not fake:
            rng -= dreamCount
            msg = redis.get("&AI"+str(rng))
            answer = "AI"
        #both mode
        elif rng > dreamCount and AI and fake:
            rng -= dreamCount
            if rng <= fakeCount:
                msg = redis.get("&fake"+str(rng))
                answer = "Fake"
            else:
                rng -= fakeCount
                msg = redis.get("&AI"+str(rng))
                answer = "AI"

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

    elif message.content.startswith('/dreamreveal') or message.content.endswith('/dr'):
        # cheat prevention
        if guessCount < players:
            await message.channel.send("This commmand is disabled while dreamplay is active")
            return

        await message.channel.send(answer)

    elif message.content.startswith('/dreamcount') or message.content.startswith('/dc'):
        await message.channel.send("Dreams: " + redis.get("&dreamcount"))
        await message.channel.send("Fake dreams: " + redis.get("&fakecount"))
        await message.channel.send("AI generated dreams: " + redis.get("&AIcount"))
        await message.channel.send("TOTAL: " + str( int(redis.get("&dreamcount")) + int(redis.get("&fakecount")) + int(redis.get("&AIcount")) ))

    elif message.content.startswith('/dreamsend') or message.content.startswith('/ds'):
        # cheat prevention
        if guessCount < players:
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

    elif message.content.startswith('/dreamname') or message.content.startswith('/dn'):
        msg = message.content.split(" ")
        total = 0
        count = int(redis.get("&dreamcount"))
        ids = []
        perPerson = defaultdict(int)

        if (len(msg) > 1):       # if name is provided
            name = msg[1]
            if name not in namesStrict:                                                # input validation
                await message.channel.send("Error: Invalid name")           # throw error to user
                return

            for i in range(count):
                if (redis.get("&dreamer" + str(i)) == name):
                    ids.append(str(i))
                    total+=1
            if total > 0:
                await message.channel.send("Count: " + str(total) + ". Dream IDs: " + (', ').join(ids))                           # inform user of all set keys
            else:
                await message.channel.send("Error: No dreams under the name " + name)
        else:       # if no name
            for i in range(count):
                perPerson[redis.get("&dreamer" + str(i))] += 1
            await message.channel.send("Count per name: ")
            msgout = ""
            for key in perPerson:
                msgout += key + ": " + str(perPerson[key]) + "\n"
            await message.channel.send(msgout)


    # Resets all global variables
    elif message.content.startswith('/dreamreset'):
        buffer = []
        guessCount = 0
        guessed = []
        guessCountUnique = 0
        namesGuessed = []
        scores = defaultdict(int)
        players = 0
        channelplaying = 0
        streaks = defaultdict(int)
        streaksBroken = 0
        correct = []
        bonus = False
        await message.channel.send("Scores reset.")

    # skip feature, also doubles as insurance encase a user puts too high of a playercount
    elif message.content.startswith('/dreamskip'):
        guessCount = 0
        guessed = []
        players = 0 
        await message.channel.send("Dream skipped.")

    # Fake function
    elif message.content.startswith('/dreamfake') or message.content.startswith('/df'):
        dreamfake = message.content.split(" ")                                   # split message
        if len(dreamfake) < 3:
            await message.channel.send("Error: Dream must be more than one word.")
            return
        fake = (' ').join(dreamfake[1:])                                        # define the dream contents
        i = 0
        while (redis.exists("&fake"+str(i))):                                  # find what numbers are taken to not override
            i+=1
        redis.set(("&fake"+str(i)), str(fake))                                # set dream
        if (i > int(redis.get("&fakecount"))):                                 # increase dream count if required
            redis.set("&fakecount", str(i))
        await message.channel.send("Fake dream {} has been added.".format(redis.get("&fakecount")))
    

    # AI function (same concept as fakes, just seperated for gamemode customizability)
    elif message.content.startswith('/dreamAI') or message.content.startswith('/dAI'):
        dreamAI = message.content.split(" ")                                   # split message
        if len(dreamAI) < 4:
            await message.channel.send("Error: AI dreams must be 3 or more words in length.")
            return
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
        if msg[2] not in namesStrict:
            await message.channel.send("Error: Invalid name provided.")
            await message.channel.send("Please use this format: `/dreamundo [dream number] [dreamer name]`")
            return
        if redis.get("&dreamer"+redis.get("&dreamcount")) == msg[2]:    # final layer of protection
            redis.delete("&dream"+redis.get("&dreamcount"))
            redis.delete("&dreamer"+redis.get("&dreamcount"))
            await message.channel.send("Dream {} by {} has been undone.".format(msg[1], msg[2]))     # inform user the entry has been removed
            # decrease dreamcount
            redis.set("&dreamcount", str(int(redis.get("&dreamcount")) - 1))

    elif message.content.startswith('/dreamdebug'):
        await message.channel.send("Buffer Length: " + str(len(buffer)) + "\n" + "Buffer Content: " + (', ').join(map(str, buffer)))
        await message.channel.send("GuessCount: " + str(guessCount) + "\n" + "Guessed: " + str(guessed))
        await message.channel.send("guessCountUnique: " + str(guessCountUnique) + "\n" + "namesGuessed: " + str(namesGuessed))
        await message.channel.send("Scores: ")
        for player, score in scores.items():
            await message.channel.send("<@{}>: {}".format(player, score))
        await message.channel.send("Players: " + str(players) + "\n" + "Channel Playing: <#" + str(channelplaying) + ">")
        await message.channel.send("Streaks: ")
        for player, streak in streaks.items():
            await message.channel.send("<@{}>: {}".format(player, streak))
        await message.channel.send("Streaks broken: " + str(streaksBroken))
        await message.channel.send("Correct: " + str(correct))
        if bonus:
            await message.channel.send("Names by score: " + keys)

    elif message.content.startswith('/dreamhelp') or message.content.startswith('/dh'):
        msgh = message.content.split(" ")                                   # split message
        if len(msgh) > 1:
            if msgh[1].capitalize() == "Bonus":
                outh = "Bonuses:\n"
                outh += "Underdog - The lowest scorer recieves +1 when they are correct and the highest scorer is incorrect. Underdog bonus scales with number of players incorrect from the top.\n"
                outh += "Streak - Recieve +1 for each correct answer on a streak of 5 or more. Streak bonus scales on streak intervals of 5.\n"
                outh += "Biggest Loser - Recieve +1 for 5 incorrect answers in a row.\n"
                outh += "Lone Wolf - If only one player is correct they recieve +1 (3+ players).\n"
                outh += "Early Bird - The fastest answer recieves +1 when they are correct and the slowest answer is incorrect.\n"
                outh += "Streak Breaker - When a streak of 5 or more is broken, all players correct recieve +1.\n"
                outh = "Rare Bonuses:\n"
                outh += "Non-conformist - Achieve Lone Wolf bonus while every incorrect player guessed the same name (4+ players).\n"
                outh += "Mixed Bag - Achieve Lone Wolf bonus while every incorrect player guessed different names (4+ players)."
                await message.channel.send(outh)

    # for scoring (must be at the bottom to not interfere with other commands)
    elif guessCount < players and message.author.id != client.user.id:

        guess = message.content
        playerID = message.author.id

        # handle debug
        if guess[0] == '&':
            playerID = guess[1]
            guess = guess[2:]

        # convert alias to name strict
        converted = False
        for sublist in aliases:
            if converted: break
            for alias in sublist:
                if converted: break
                if (guess.capitalize() == alias or guess.upper() == alias):
                    guess = sublist[0]
                    converted = True

        # prevent double guess, and don't count non-name guesses
        if playerID in guessed or not converted:
            return
        else:           # let the user know their vote was counted
            await message.add_reaction("✅")
                    
        if guess.lower() == answer.lower():
            if playerID not in scores:
                scores[playerID] = 0
            scores[playerID] += 1
            streaks[playerID] += 1
            correct.append(playerID)
        else:
            if playerID not in scores:
                scores[playerID] = 0
            if streaks[playerID] > 0:
                streaks[playerID] = 0
                if streaks[playerID] >= 5:
                    streaksBroken += 1
            else:
                streaks[playerID] -= 1

        guessed.append(playerID)
        guessCount += 1
        if guess.lower() not in namesGuessed:
            guessCountUnique += 1
            namesGuessed.append(guess.lower())

        if guessCount >= players:
            channel = client.get_channel(channelplaying)

            # evaluate bonuses
            if bonus:
                bonusMsg = "BONUSES:\n"
                streakMsg = ""
                breakerMsg = ""
                scores = {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}            # --- sort scores - https://stackoverflow.com/questions/52141785/sort-dict-by-values-in-python-3-6
                keys = list(scores.keys())
                # underdog bonus
                i = 0
                while (keys[-1] in correct) and (keys[i] not in correct) and (keys[-1] != keys[i]):
                    scores[keys[-1]] += 1
                    i += 1
                if i == 1:
                    bonusMsg += "Underdog: <@{}>\n".format(keys[-1])
                elif i > 1:
                    bonusMsg += "Underdog: <@{}> (x{})\n".format(keys[-1], (i))
                # streak bonus and Biggest Loser
                for player, streak in streaks.items():
                    if streak >= 5:
                        scores[player] += streak//5
                        streakMsg += "<@{}> ({}), ".format(player, streak)
                    elif streak <= -5:
                        scores[player] += 1
                        streaks[player] = 0
                        bonusMsg += "Biggest Loser: <@{}>\n".format(player)
                if streakMsg:
                    bonusMsg += ("Streaks: " + streakMsg + "\n")
                # Lone wolf bonus
                if len(correct) == 1 and players >= 3:
                    scores[correct[0]] += 1
                    bonusMsg += "Lone Wolf: <@{}>\n".format(correct[0])
                # Non-conformist bonus
                if len(correct) == 1 and len(namesGuessed) == 2 and players >= 4:
                    scores[correct[0]] += 1
                    bonusMsg += "Non-conformist: <@{}>\n".format(correct[0])
                # Mixed Bag bonus
                if len(correct) == 1 and len(namesGuessed) == players and players >= 4:
                    scores[correct[0]] += 1
                    bonusMsg += "Mixed Bag: <@{}>\n".format(correct[0])
                # Early bird bonus
                if guessed[0] in correct and guessed[-1] not in correct:
                    scores[guessed[0]] += 1
                    bonusMsg += "Early Bird: <@{}>\n".format(guessed[0])
                # streak broken bonus
                if streaksBroken > 0 and len(correct) > 0:
                    for player in correct:
                        scores[player] += 1
                        breakerMsg += "<@{}>, ".format(player)
                    bonusMsg += ("Streak Breakers: " + breakerMsg + "\n")

            # auto reveal and show sorted scores
            scores = {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
            keys = list(scores.keys())
            msg = answer
            scoreMsg = "Answer: " + msg + "\n" + "Scores: \n"  
            for player, score in scores.items():
                if player in correct:
                    scoreMsg += ("🟢<@{}>: {} ".format(player, score))
                else:
                    scoreMsg += ("🔴<@{}>: {} ".format(player, score))
                # point emojis
                if player in scoresPrev and player in scoresPrevKeys:
                    scoreDiff = score - scoresPrev[player]
                    if scoreDiff > 1:
                        scoreMsg += ("{}".format(emojiNums[scoreDiff]))
                    indexDiff = keys.index(player) - scoresPrevKeys.index(player)
                    if indexDiff < 0:
                        scoreMsg += ("⬆️\n")
                    elif indexDiff > 0:
                        scoreMsg += ("⬇️\n")
                else:
                    scoreMsg += ("\n")
                    
            await channel.send(scoreMsg)

            # bonus messages (only send if anything has been added to the message)
            if bonus and bonusMsg != "BONUSES:\n":
                await channel.send(bonusMsg)

            # reset
            guessed = []
            streaksBroken = 0
            correct = []
            bonusMsg = ""
            streakMsg = ""
            breakerMsg = ""
            guessCountUnique = 0
            namesGuessed = []
            scoresPrev = scores
            scoresPrevKeys = list(scoresPrev)


client.run(os.environ['BOT_TOKEN'])       #token to link code to discord bot, replace "os.environ['BOT_TOKEN']" with your token