import discord

import logging
import logging.handlers
from random import random
import random as rnd

from bot_variables import BotVariables
import commands
import get_ai_response as ai
import tasks

from numpy.random import choice


# Declare logger
LOGGER = logging.getLogger("invalid")
LOGGER.setLevel(logging.INFO)

handler = logging.handlers.RotatingFileHandler(
    filename="discord.log",
    encoding="utf-8",
    maxBytes=33_554_432,  # 32 MiB
    backupCount=5,
)

dt_fmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter("[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{")
handler.setFormatter(formatter)

LOGGER.addHandler(handler)

ai.LOGGER = commands.LOGGER = tasks.LOGGER = LOGGER


# Retrieve sensitive information from an unlisted file
TOKEN: str
OPENROUTER_API_KEY: str

with open("tokens.txt", "r") as file:
    temp = file.read().splitlines()
    TOKEN = temp[0]
    OPENROUTER_API_KEY = temp[1]

LOGGER.info("Read tokens from file")


# Declare the bot
intents = discord.Intents.default()
intents.guild_typing = True
intents.message_content = True
intents.guild_reactions = True

client = discord.Client(intents=intents)

LOGGER.info("Declared Discord client")


# Read saved info from a file if it exists
bot_vars: BotVariables

try:
    bot_vars = BotVariables.from_file("data/bot_vars.csv")
    LOGGER.info("Read bot_vars from file")
except FileNotFoundError as e:
    LOGGER.info("Tried reading bot_vars from file but it doesn't exist, using default constructor")
    bot_vars = BotVariables()
except Exception as e:
    LOGGER.error(f"Exception while reading bot vars: {e}")
    bot_vars = BotVariables()

bot_vars.ai_key = OPENROUTER_API_KEY
bot_vars.client = client

commands.bot_vars = tasks.bot_vars = bot_vars


# Print a message when the bot is up
@client.event
async def on_ready():
    LOGGER.info(f'We have logged in as {client.user}')
    client.loop.create_task(tasks.presence_task())
    client.loop.create_task(tasks.save_on_disk_task())
    print("Bot is fully ready")


# Declare commands
@client.event
async def on_message(message: discord.Message):
    global bot_vars

    if message.author == client.user:
        return


    await commands.process_tokens_info(message)

    await commands.check_if_waiting_for_message(message)

    try:
        msg_first_word: str = message.content.split()[0].lower()
    except IndexError:
        LOGGER.info(f"Tried splitting user message but it has no text content")
        return

    match msg_first_word:
        case ";prompt":
            await commands.prompt(message)

        case ";set-message-interval":
            await commands.set_message_interval(message)
        
        case ";set-own-message-memory":
            await commands.set_own_message_memory(message)
        
        case ";clear-memory":
            await commands.clear_memory(message)

        case ";stop-writing-here" | ";stop":
            await commands.stop_writing_here(message)

        case ";status":
            await commands.status(message)

        case ";tokens" | ";tok" | ";token" | ";balance" | ";bal":
            await commands.tokens(message)
        
        case ";pay":
            await commands.pay(message)
        
        case ";upgrades" | ";upgrade":
            await commands.upgrades(message)
        
        case ";blackjack" | ";bj":
            await commands.blackjack(message)
        
        case ";slots-legacy" | ";slot-legacy" | ";sl" | ";slots" | ";slot":
            await commands.slots(message)

        case ";slots-pirots" | ";slot-pirots" | ";pirots" | ";pirot" | ";sp":
            await commands.slots_pirots(message)

        case ";leaderboard" | ";leaderboards" | ";lb" | ";top":
            await commands.leaderboard(message)

        case ";translate" | ";tl":
            await commands.translate(message)

        case ";coinflip" | ";cf":
            await message.reply(f":coin: {'Орёл' if random() >= 0.5 else 'Решка'}")

        case ";ping":
            await message.channel.send('pong')

        case ";help":
            await commands.help(message)
        
        case ";hesoyam":
            if message.author.guild_permissions.administrator:
                bot_vars.user_interaction_tokens[message.author.id][0] += 250000
                await message.channel.send("CHEAT CODE ACTIVATED")

        case ";kaching":
            if message.author.guild_permissions.administrator:
                bot_vars.user_interaction_tokens[message.author.id][0] += 1000
                await message.channel.send("CHEAT CODE ACTIVATED")

        case ";antihesoyam":
            if message.author.guild_permissions.administrator:
                if bot_vars.user_interaction_tokens[message.author.id][0] >= 50000:
                    bot_vars.user_interaction_tokens[message.author.id][0] -= 50000
                    await message.channel.send("CHEAT CODE ACTIVATED")
                else:
                    bot_vars.user_interaction_tokens[message.author.id][0] = 0
                    await message.channel.send("CHEAT CODE ACTIVATED")

        case ";birb":
            await message.channel.send(choice(['<:High1:1410726957259161793>', '<:High2:1408765844296826990>', \
                                              '<:High3:1410726975454056488>', '<:High4:1410726991644065842>', \
                                               '<:Pride:1380228659658493972> '], 1, p = [0.2475, 0.2475, 0.2475, 0.2475, 0.01])[0])

        case ";summon-pig" | ";summon" | "вызвать":
            if message.content.lower().startswith(
                    (";summon-pig", ";summon pig", "вызвать свинью")):  # This is so scuffed, I'm sorry
                await commands.summon_pig(message)

        case ";tax":
            if bot_vars.user_interaction_tokens[message.author.id][0] > 0:
                bot_vars.user_interaction_tokens[message.author.id][0] -= 100
                await message.channel.send(f"Вы заплатили налог. Осталось {bot_vars.user_interaction_tokens[message.author.id][0]} :coin:")
            else:
                await message.channel.send("Вы слишком нищий для уплаты налога.")

        case ";resurrect":
            await message.channel.send("# П̶̡̮͈̹̻̣̰͓͔̂̎͐̈́͝р̵͉͙͚̟̝̞̬̋̎͜о̸̗̮̬̟̎̏͆̅͐̋̊͛̀̀̀̀̅̕͝в̴̢̳̗͔̀̌̍̋̔͒͊̅͌̚͠о̷͙̙̖̟̪̬̐̊̓͒͌͒̓͑͗̅͜͝д̶̨̛̱͕͕̩̜͓̬̏͊̎̈͐̅͗̇͌̓̆͋̐̕ͅи̸̛̳̖̙̼͖͚̙̩͚̥͙̪͊̀̐̓͗̾̃̔̎̔̚ͅт̶̢̳̫̹̙͌͐̌͗͘с̵̛̙̹͎͕̤̠̦̜͕͎̻͊͆̋̌͜͜я̸̛͈̰̘͎̟̪̰̟̒̌̀͛̅̉͛̀͗ ̶̡̳̱̤͎́͋̐̾̅̏͜р̵̧͇̏͝и̶̥̦̪̠͓͙̣̪́̈̿̈͂̓͘͜͝т̵̭̣̹̩̞͙͖͕͕̪̼̯̤̥͑͗̔́̄̆̔͜͝у̵̨͉̫̗̣̫̍̇̀̇̚͝а̵̭̹͉̳̙̭̩͆̏̈́̈́̑̔̈́̀͛̄л̸̨̲̙̻̟͔̦̍̉̈́̔̊̐̉͛̈͠͠")
            bot_vars.write_to_file("data/bot_vars.csv")
            LOGGER.info("Saved bot_vars to a file")
            await quit()

        case _:
            await commands.automessage(message)



# Run the bot
client.run(TOKEN, log_handler=handler)
