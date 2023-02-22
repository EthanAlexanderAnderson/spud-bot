from pickle import TRUE
import discord
from discord.ext import commands
import redis
import random
import os
from collections import defaultdict
from dreamgame.dreamhelp import dreamhelp
from dreamgame.dreamcensor import dreamcensor
from dreamgame.calc import calcRatio
from dreamgame.calc import calcSkillRating

# -- global variables --
redis = redis.Redis.from_url(os.environ['REDIS_URL'], decode_responses=True)    # loads redis server, replace "os.environ['REDIS_URL']" with your redis URL
client = commands.Bot(command_prefix='/', intents=discord.Intents.all())        # command prefix (/)

# global variables for dream journal game
namesStrict = ["Ethan", "Nathan", "Cole", "Max", "Devon", "Oobie", "Eric", "Dylan", "Adam", "Mitch", "Jack", "Zach", "Devo", "Eddie"]
names = ["Ethan", "Ham", "Anderson", "Oobie", "Oob", "Larose", "Nathan", "Nash", "Nate", "Nashton", "Skrimp", "Ashton", "Eric", "Ric", "Rick", "Mitch", "Mitchell", "Max", "Maxwell", "Mac", "Macs", "MTG", "MT", "Cole", "Devon", "Devo", "Deevi", "Shmev", "Eddie", "Edmund", "Ed", "Adam", "Chad", "Chadam", "Dylan", "Teddy", "Jack", "Jac", "Jak", "Zach", "Zack", "Zac", "Zak", "Zachary", "AI", "Fake"]
aliases = [["Ethan", "Anderson", "Ethan A", "Ham", "Hammie", "Hammy", "Eman", "Eman826", "Et", "Eth", "Etha", "Ander", "Ea"], ["Cole", "Coal", "Cole H", "Justin", "Pokerstars", "Col", "Co", "Ch", "C"], ["Nathan", "Asthon", "Nathan A", "Nash", "Nate", "Nashton", "Skrimp", "Big Skrimp", "Bs", "Nat", "Na", "N"], ["Oobie", "Stew", "Oobie Stew", "Oob", "Scoobie", "Beta", "Weeb", "Larose", "Ethan Larose", "Ethan L", "Os", "Ob", "O"], ["Eric", "Linguine", "Eric L", "Ric", "Rick", "El"], ["Mitch", "Mitchell", "Ms"], ["Max", "Max K", "Maxwell", "Maxwel", "Maximillion", "Mac", "Macs", "Mtg", "Mt", "Mk"], ["Devon", "Devon C", "Dev", "Dc"], ["Devo", "Devo S", "Devon S", "Deevi", "Shmev", "Ds"], ["Eddie", "Edmund", "Ed", "Eb"], ["Adam", "Adam G", "Chad", "Chadam", "Graf", "Ag", "A"], ["Dylan", "Dylan C", "Teddy", "Ted", "Cam", "Lz", "T"], ["Jack", "Jack M", "Jack Mac", "Jac", "Jak", "Jm", "J"], ["Zach", "Zach R", "Zack", "Zac", "Zak", "Zachary", "Zr", "Z"], ["Ai", "Bot", "Chester"], ["Fake", "Fak", "Fa", "F"], ["Gnome", "Gnom", "Gno", "Gn", "G"]]
emojiNums = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
adminID = 0
answer = ""
buffer = []
browseMsg = 0
deleteConfirmationMsg = 0
guessCount = 0
guessCountUnique = 0
namesGuessed = []
guessed = []
scores = defaultdict(int)
scoresPrev = defaultdict(int)
players = 0
channelplaying = 0
dreamMsg = 0
roundOver = False
# flags
censor = fake = AI = gnome = False
# bonus variables
streaks = defaultdict(int)
streaksBroken = 0
correct = []
bonus = False
bottomStreak = ['', 0]

def dreamplay(msg): 
    global answer, buffer, guessCount, guessCountUnique, guessed, players, bonus, roundOver
    global censor, fake, AI, gnome 
    guessCount = 0
    guessed = []
    roundOver = False
    dreamCount = int(redis.get("&dreamcount"))
    fakeCount = int(redis.get("&fakecount"))
    AICount = int(redis.get("&AIcount"))

    # check for flags and set variables
    if (len(msg) > 1):
        censor = False
        fake = False
        AI = False
        gnome = False
        bonus = False
        players = 0
        if msg[1].isdigit():
            players = int(msg[1])
        if ('C' in msg or 'c' in msg):
            censor = True
        if ('F' in msg or 'f' in msg):
            fake = True
        if ('AI' in msg or 'ai' in msg or 'Ai' in msg):
            AI = True
        if ('B' in msg or 'b' in msg):
            bonus = True
        if ('G' in msg or 'g' in msg):
            gnome = True

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
        msg = dreamcensor(msg.split(" "), names)

    # gnome mode
    split = msg.split(" ")
    gnomeChance = random.randint(0, 4)
    # gnome only applies to dreams of 16 word length or more     
    if gnome and len(split) > 16 and gnomeChance == 0:
        # gnome is placed in the back half of the dream, but never the very end
        for i in range (len(split)//2,len(split)-5):
            if len(split[i]) == 5:
                split[i] = "gnome"
                answer = "Gnome"
                break
        msg = (" ").join(split)

    # return dream to display
    return (">>> " + msg)


# -- Bot Functionality --
@client.event                                                                   # tell console when bot is ready
async def on_ready():
    print('Bot is ready.')


@client.event
async def on_reaction_add(reaction, user):
    global adminID, dreamMsg, browseMsg, browseIndex, browseList, browseUser, deleteConfirmationMsg

    if reaction.message.author.id == client.user.id:
        # reaction to start new round in dreamplay
        if (reaction.emoji == "⏩") and user.id == adminID:
            dreamMsg = await reaction.message.channel.send(dreamplay(["/dp"]))
            await dreamMsg.add_reaction("⏩")
        # profile dream browser
        elif reaction.message == browseMsg and user.id != client.user.id:
            deleteConfirmationMsg = 0
            if (reaction.emoji == "⬆️"):
                # first
                browseIndex = 0
                try:
                    await browseMsg.remove_reaction("⬆️", user)
                except Exception:
                    pass
            elif (reaction.emoji == "⬅️"):
                # back
                browseIndex -= 1
                try:
                    await browseMsg.remove_reaction("⬅️", user)
                except Exception:
                    pass
            elif (reaction.emoji == "➡️"):
                # forward
                browseIndex += 1
                try:
                    await browseMsg.remove_reaction("➡️", user)
                except Exception:
                    pass
            elif (reaction.emoji == "⬇️"):
                # last
                browseIndex = len(browseList)-1
                try:
                    await browseMsg.remove_reaction("⬇️", user)
                except Exception:
                    pass
            elif (reaction.emoji == "🗑️" and user.id == browseUser):
                deleteConfirmationMsg = await browseMsg.channel.send("Are you sure you want to delete dream #{}?".format(str(browseList[browseIndex]))) 
                await deleteConfirmationMsg.add_reaction("🗑️")
            await browseMsg.add_reaction("🗑️")
            # edit dream browser based on control usage
            await browseMsg.edit(content=">>> **ID: " + str(browseList[browseIndex]) + "\n** " + redis.get("&dream" + str(browseList[browseIndex])) + " \n")
        # confirmation for dream deletion
        elif reaction.message == deleteConfirmationMsg and user.id == browseUser:
            deleteID = browseList[browseIndex]
            redis.delete("&dream" + str(deleteID))
            redis.delete("&dreamer" + str(deleteID))
            del browseList[-1]
            await deleteConfirmationMsg.channel.send("Dream #" + str(deleteID) + " has been deleted.")


@client.event
async def on_message(message):                                                  # read sent message
    global adminID, answer, buffer, count, guessCount, guessCountUnique, namesGuessed, guessed, scores, scoresPrev, scoresPrevKeys, players, channelplaying, streaks, streaksBroken, correct, bonus, keys, roundOver, dreamMsg, browseMsg, browseIndex, browseList, browseUser, deleteConfirmationMsg
    global censor, fake, AI, gnome

    if message.content.startswith('/send '):                                    # for /send
        keyword = message.content.split(" ")                                    # split incoming message
        msg = redis.get((' ').join(keyword[1:]))                                # find tag in dictionary
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
        # just to help people who accidentally use "/dreamadd fake" instead of "/dreamfake"
        if dreamer == "Fake":
            i = 0
            while (redis.exists("&fake"+str(i))):                               # find what numbers are taken to not override
                i+=1
            redis.set(("&fake"+str(i)), str(dream))                              # set dream
            if (i > int(redis.get("&fakecount"))):                              # increase dream count if required
                redis.set("&fakecount", str(i))
            await message.channel.send("Fake dream {} has been added.".format(redis.get("&fakecount")))
            return
        # if name not given, check profiles
        elif dreamer not in namesStrict:                                        # input validation
            if redis.exists("&" + str(message.author.id)):
                dreamer = (redis.get("&" + str(message.author.id)))
                dream = (' ').join(dreamadd[1:])
            else:
                await message.channel.send("Error: Invalid dreamer name / missing profile")           # throw error to user
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
        channelplaying = message.channel.id
        adminID = message.author.id
        msg = message.content.split(" ")
        dreamMsg = await message.channel.send(dreamplay(msg))             # sends dream
        await dreamMsg.add_reaction("⏩")
        profileKeys = redis.keys(pattern='%*')
        browseMsg = 0


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
            perPerson = {k: v for k, v in sorted(perPerson.items(), key=lambda x: x[1], reverse=True)}            # --- sort scores - https://stackoverflow.com/questions/52141785/sort-dict-by-values-in-python-3-6
            await message.channel.send("Count per name: ")
            msgout = ""
            for key in perPerson:
                msgout += key + ": " + str(perPerson[key]) + "\n"
            await message.channel.send(msgout)


    # Resets all global variables
    # TODO remove AFTER adding reset emoji reaction control (with confirmation)
    elif message.content.startswith('/dreamreset'):
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

    # phased out for delete function in profile dream browser, keeping command for legacy
    elif message.content.startswith('/dreamundo') or message.content.startswith('/du'):
        # check if undoer has same ID as most recent dream added
        if redis.get("&dreamer"+redis.get("&dreamcount")) == redis.get("&" + str(message.author.id)):
            await message.channel.send("Dream {} by {} has been undone.".format(redis.get("&dreamcount"), "<@" + str(message.author.id) + ">"))     # inform user the entry has been removed
            redis.delete("&dream"+redis.get("&dreamcount"))
            redis.delete("&dreamer"+redis.get("&dreamcount"))
            # decrease dreamcount
            redis.set("&dreamcount", str(int(redis.get("&dreamcount")) - 1))
        else:
            await message.channel.send("The most recent dream is not yours. You cannot undo it")

    # a bunch of variables used for debugging
    elif message.content.startswith('/dreamdebug'):
        debugMsg = ""
        debugMsg += ("Admin: <@" + str(adminID) + ">\n")
        debugMsg += ("Buffer Length: " + str(len(buffer)) + " : " + (', ').join(map(str, buffer)) + "\n")
        debugMsg += ("GuessCount: " + str(guessCount) + " : " + str(guessed) + "\n")
        debugMsg += ("guessCountUnique: " + str(guessCountUnique) + " : " + str(namesGuessed) + "\n")
        debugMsg += ("Scores:\n")
        for player, score in scores.items():
            debugMsg += ("<@{}>: {}\n".format(player, score))
        debugMsg += ("Players: " + str(players) + "\n")
        debugMsg += ("Channel Playing: <#" + str(channelplaying) + ">\n")
        debugMsg += ("Streaks:\n")
        for player, streak in streaks.items():
            debugMsg += ("<@{}>: {}\n".format(player, streak))
        debugMsg += ("Streaks broken: " + str(streaksBroken) + "\n")
        debugMsg += ("Correct: " + str(correct) + "\n")
        await message.channel.send(debugMsg)

    # also for debugging
    elif message.content.startswith('/dreamkeys'):
        msg = message.content.split(" ")
        if msg[1] == '%':
            keys = redis.keys(pattern='%*')
        else:
            keys = redis.keys(pattern='&*')
        fullKeys = (', ').join(sorted(keys))
        length = len(fullKeys)
        i = 0
        while length > 1999:
            await message.channel.send(fullKeys[i:i+1999])
            i = i + 1999
            length = length - 1999
        await message.channel.send(fullKeys)


    elif message.content.startswith('/dreamhelp') or message.content.startswith('/dh'):
        await message.channel.send(dreamhelp(message.content.split(" ")))

    elif message.content.startswith('/dreamleave') or message.content.startswith('/dl'):
        msg = message.content.split(" ")
        leaver = 0
        # force another user to leave
        if message.author.id == adminID and len(msg) > 1:
            target = msg[1]
            leaver = target[2:-1]
        # command user leaves
        elif message.author.id in scores:
            leaver = message.author.id
        scores.pop(leaver)
        streaks.pop(leaver)
        # if the admin left, assign new admin
        if message.author.id == adminID and message.author.id not in scores:
            adminID = list(scores.keys())[0]
            await message.channel.send("<@{}> is the new admin.".format(adminID))
        players -= 1
        await message.channel.send("<@{}> has left the game.".format(leaver))

    elif message.content.startswith('/dreamprofile') or message.content.startswith('/profile') or message.content == ('/dream') or message.content == ('/d'):
        msg = message.content.split(" ")                                   # split message
        if len(msg) <= 2:
            # profile displaying
            # stats:  dreamcount, all time score (exp), correct ratio, longest streak
            # if name provided is in names strict, show profile of that user
            if len(msg) == 2 and msg[1][0] == "<":
                # provided @
                userID = msg[1][2:-1]
                name = redis.get("&" + str(userID))
                await message.channel.send("Profile <@" + str(userID) + "> is assigned to " + name)
            elif len(msg) == 2 and msg[1] in namesStrict:
                # provided name
                name = msg[1]
                userID = 0
                await message.channel.send("Profile for " + name)
            else:
                # nothing provided (return profile of sender)
                userID = message.author.id
                name = redis.get("&" + str(userID))
                await message.channel.send("Your profile <@" + str(userID) + "> is assigned to " + name)
            # fetch and display stats
            stats = redis.get("%" + name).split(",")
            ratio = calcRatio(stats, 0, 1)
            # skill rating formula: ratio * ((#correct / 10) + longest streak)
            statsMsg = "**Skill Rating: " + str(calcSkillRating(stats, ratio)) + "**"
            statsMsg += "\nTotal Corrects: " + stats[0]
            statsMsg += "\nTotal Incorrects: " + stats[1]
            statsMsg += "\nRatio: " + str(ratio) + "%"
            statsMsg += "\nLongest Streak: " + stats[2]
            statsMsg += "\nMemory: " + str(calcRatio(stats, 4, 5)) + "%"
            statsMsg += "\nGnome Count: " + stats[3]
            await message.channel.send(statsMsg)
            # load dream browser
            browseMsg = await message.channel.send("Loading your dream browser, please wait")
            count = int(redis.get("&dreamcount"))
            browseList = []
            browseIndex = 0
            browseUser = userID
            deleteConfirmationMsg = 0
            for i in range(count+1):
                if (redis.get("&dreamer" + str(i)) == name):
                    browseList.append(i)
            # controls for dreambrowser, function for this near top
            await browseMsg.edit(content="Use these reaction controls to browse your dreams. Count: " + str(len(browseList)))
            await browseMsg.add_reaction("⬆️")
            await browseMsg.add_reaction("⬅️")
            await browseMsg.add_reaction("➡️")
            await browseMsg.add_reaction("⬇️")

        elif len(msg) > 2 and (msg[1].lower() == 'link' or msg[1].lower() == 'add') and msg[2].capitalize() in namesStrict:
            # profile linking
            name = msg[2]
            if len(msg) == 3:
                # if 1 == link and 2 in names strict, link user id to that name
                userID = message.author.id
            elif len(msg) == 4:
                # if 1 == link and 2 in names strict and 3 is a user id, link that user id to that name
                userID = msg[3]
            redis.set("&" + str(userID),(name))
            await message.channel.send("Profile <@" + str(userID) + "> has been assigned to " + name)
            
    # skill rating formula: ratio * ((#correct / 10) + longest streak)
    elif message.content.startswith('/dreamleaderboard') or message.content.startswith('/leaderboard') or message.content.startswith('/db') or message.content.startswith('/lb'):
            profileKeys = redis.keys(pattern='%*')
            leaderboard = defaultdict(int)
            for i in profileKeys:
                stats = redis.get(i).split(",")
                # add tiny number to prevent 0 division
                ratio = calcRatio(stats, 0, 1)
                leaderboard[i[1:]] = calcSkillRating(stats, ratio)
            leaderboard = {k: v for k, v in sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)}
            leaderboardMsg = ""
            i = 0
            for player, score in leaderboard.items():
                if score > 0:
                    if i == 0:
                        leaderboardMsg += ":first_place: ***" + str(player) + ": " + str(score) + "***\n"
                    elif i == 1:
                        leaderboardMsg += ":second_place: **" + str(player) + ": " + str(score) + "**\n"
                    elif i == 2: 
                        leaderboardMsg += ":third_place: **" + str(player) + ": " + str(score) + "**\n"
                    elif i < 10:
                        leaderboardMsg += "{} {}: {}\n".format(emojiNums[i], str(player), str(score))
                    else:
                        leaderboardMsg += ":asterisk: " + str(player) + ": " + str(score) + "\n"
                    i += 1
            leaderboardMsg += "(skipped zero-rated players)"
            await message.channel.send(leaderboardMsg)


    # for scoring (must be at the bottom to not interfere with other commands)
    elif guessCount < players and message.author.id != client.user.id and roundOver == False:

        guess = message.content
        playerID = message.author.id
        debug = False

        # handle debug players
        if guess[0] == '&':
            playerID = guess[1]
            guess = guess[2:]
            debug = True

        # capitalize for standardization
        guess = guess.capitalize()

        # convert alias to name strict
        converted = False
        for sublist in aliases:
            if converted: break
            for alias in sublist:
                if converted: break
                if guess == alias:
                    guess = sublist[0]
                    converted = True

        # prevent double guess, and don't count non-name guesses
        if playerID in guessed or not converted:
            return
        elif (guess == "Fake" and fake == False) or (guess == "AI" and AI == False) or (guess == "Gnome" and gnome == False):
            await message.add_reaction("⛔")
            return
        else:           # let the user know their vote was counted
            await message.add_reaction("✅")

        # add new player to score list
        if playerID not in scores:
            scores[playerID] = 0  

        # prepare profile stats, if statements are here to not trigger error
        if not debug:
            name = redis.get("&" + str(playerID))
            if name in namesStrict:
                stats = redis.get("%" + name).split(",")

        # give score for corect answer
        if guess == answer:
            scores[playerID] += 1
            streaks[playerID] += 1
            correct.append(playerID)
            # profile stats correct & longest streak
            if not debug and name in namesStrict:
                stats[0] = str(int(stats[0]) + 1)
                if streaks[playerID] > int(stats[2]):
                    stats[2] = str(streaks[playerID])
                if name == answer:
                    stats[4] = str(int(stats[4]) + 1)
                redis.set("%" + name, (",").join(stats))

        else:
            if streaks[playerID] > 0:
                if streaks[playerID] >= 5:
                    streaksBroken += 1
                streaks[playerID] = 0
            else:
                streaks[playerID] -= 1
            # profile stats incorrect
            if not debug and name in namesStrict:
                stats[1] = str(int(stats[1]) + 1)
                if name == answer:
                    stats[5] = str(int(stats[5]) + 1)

                if gnome and answer == "Gnome":
                    scores[playerID] -= 10
                    if scores[playerID] < 0:
                        scores[playerID] = 0
                    # track gnome stats
                    stats[3] = str(int(stats[3]) + 1)

                redis.set("%" + name, (",").join(stats))

        # tracking who guessed and what they guessed
        guessed.append(playerID)
        guessCount += 1
        if guess not in namesGuessed:
            guessCountUnique += 1
            namesGuessed.append(guess)

        # update guess count on dream msg
        if guessCount <= 10: # prevent index error
            await dreamMsg.add_reaction("{}".format(emojiNums[guessCount - 1]))

        if guessCount == players and len(guessed) > 0:
            channel = client.get_channel(channelplaying)
            roundOver = True

            # evaluate bonuses
            # TODO late joiner bonus (enough to be competitive, but not enough to easily pass last place)
            if bonus:
                bonusMsg = "**BONUSES:**\n"
                streakMsg = ""
                breakerMsg = ""
                ironyMsg = ""
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
                # bottom feeder bonus
                if keys[-1] == bottomStreak[0]:
                    bottomStreak[1] += 1
                else:
                    bottomStreak[0] = keys[-1]
                    bottomStreak[1] = 0
                if bottomStreak[1] >= 5 and (bottomStreak[1]%5 == 0):
                    scores[bottomStreak[0]] += 1
                    bonusMsg += "Bottom Feeder: <@{}>\n".format(bottomStreak[0])
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
                # Irony bonus
                irony = False
                for player in guessed:
                    if redis.get("&" + str(player)) == answer and player not in correct:
                        irony = True
                if irony and len(correct) > 0:
                    for player in correct:
                        scores[player] += 1
                        ironyMsg += "<@{}>, ".format(player)
                    bonusMsg += ("Irony Bonus: " + ironyMsg + "\n")

            # gnome mode
            gnomeMsg = "**GNOMED:** "
            if gnome and answer == "Gnome":
                for player in guessed:
                    if player not in correct:
                        gnomeMsg += "<@{}>, ".format(player)

            # auto reveal and show sorted scores
            scores = {k: v for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)}
            keys = list(scores.keys())
            msg = answer
            scoreMsg = "**Answer:** " + msg + "\n" + "**Scores:** \n"  
            for player, score in scores.items():
                # scoreboard emojis
                if player in scoresPrev and player in scoresPrevKeys:
                    scoreDiff = score - scoresPrev[player]
                    indexDiff = keys.index(player) - scoresPrevKeys.index(player)
                else:
                    scoreDiff = (score-1)
                    indexDiff = 0
                if indexDiff < 0:
                    scoreMsg += ("⬆️")
                elif indexDiff > 0:
                    scoreMsg += ("⬇️")
                else:
                    scoreMsg += ("⬛")
                if player in correct and bonus:
                    scoreMsg += ("{}<@{}>: {} ".format(emojiNums[scoreDiff], player, score))
                elif player in correct and not bonus:
                    scoreMsg += ("🟢<@{}>: {} ".format(player, score))
                elif gnome and answer == "Gnome":
                    scoreMsg += ("👺<@{}>: {} ".format(player, score))
                else:
                    scoreMsg += ("🔴<@{}>: {} ".format(player, score))
                scoreMsg += ("\n")
                    
            await channel.send(scoreMsg)

            # bonus messages (only send if anything has been added to the message)
            if bonus and bonusMsg != "**BONUSES:**\n":
                await channel.send(bonusMsg)
            # only send message if someone was gnomed
            if gnome and gnomeMsg != "**GNOMED:** ":
                await channel.send(gnomeMsg)

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