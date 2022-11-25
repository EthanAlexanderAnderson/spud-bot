import random
import discord
from discord.ext import commands
import redis

def dreamplay(msg, message):  
    guessCount = 0
    guessed = []
    roundOver = False
    dreamCount = int(redis.get("&dreamcount"))
    fakeCount = int(redis.get("&fakecount"))
    AICount = int(redis.get("&AIcount"))
    # check for flags and set variables
    if (len(msg) > 1):
        if ('N' not in msg and 'n' not in msg): # dont reset flags if /dp n is used. n meaning next round
            censor = False
            fake = False
            AI = False
            gnome = False
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

    # gnome mode
    split = msg.split(" ")
    gnomeChance = random.randint(0, 4)     
    if gnome and len(split) > 16 and gnomeChance == 0:
        for i in range (len(split)//2,len(split)-5):
            if len(split[i]) == 5:
                split[i] = "gnome"
                answer = "Gnome"
                break
        msg = (" ").join(split)
    return msg