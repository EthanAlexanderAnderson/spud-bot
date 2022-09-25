# spud-bot

# Spam Post User Database - Discord Bot

## Commands:
[Square Bracket] = Required Flag,   (Round Bracket) = Optional Flag

- /add [key] [link] - Adds image

- /send [key] - Sends image

- /remove [key] - Removes images

- /list - Lists all images keys

## Dream Journal Game Commands:

- /dreamplay (#) (c) (f) (AI) (b) - Get a random dream. # = Number of players, c = Censor names, f = Include fake dreams, AI = Include AI dreams, b = include bonus points

- /dreamreveal - Reveal the dreamer of the random dream

- /dreamadd [dreamer name] [dream] - Add a dream to the database

- /dreamfake [fake dream] - Add a fake dream for the alternative gamemode

- /dreamAI [AI dream] - Add an AI generated dream for the alternative gamemode

- /dreamcount - Number of dreams in the database

- /dreamsend [number] (Fake/AI) - Sends the dream and dreamer of corresponding number ID

- /dreamname (name) - Sends all number IDs of dreams belonging the dreamer name provided. If no name is provided it will send the number of dreams belonging to each name.

- /dreamreset - Resets scores and buffer (for auto scoring)

- /dreamundo [number] [name] - Undo most recently added dream. Number and name required to prevent an accidental undo.

Most dream commands have abbreviated forms, for example, you can type /dp instead of /dreamplay

My bot is run using a Heroku free server.
