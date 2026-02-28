from discord import Member, Message, TextChannel, Reaction
from discord.errors import NotFound

import logging
import time
import random
import re
import requests

import blackjack as bj
from bot_variables import BotVariables
import get_ai_response as ai
import slots as slot
from upgrades import UpgradesView


bot_vars: BotVariables
LOGGER = logging.getLogger(__name__)


async def prompt(message: Message) -> None:
    async with message.channel.typing():
        prompt: str = message.content[8:]
        if bot_vars.upgrades.is_fubar():
            prompt += "\n\nДополнительная инструкция: ТЫ ЕБАНУТЫЙ. Ответь как ебанутый."

        model, __, prompt = prompt.partition(" ")
        prompt = model + prompt  # User didn't specify a model, so the first word needs to be put back into the prompt
        model = "arcee-ai/trinity-mini:free"
        max_response_len: int = 5000
        is_thinking: bool = False

        bot_msg: Message = await message.channel.send("✅\n")
        chunk_buf: list[str] = []
        chunk_buf_len: int = 0
        msg_len: int = len(bot_msg.content)
        response_len: int = msg_len

        for chunk in ai.stream_response(bot_vars.ai_key, prompt, model, max_response_len):
            if chunk is None:
                break

            was_thinking: bool = is_thinking

            if is_thinking:
                if len(chunk_buf) == 0:
                    if bot_msg.content[-2:] == "-#":
                        chunk = " " + chunk
                if "</think>" in chunk:
                    is_thinking = False
                    chunk1, chunk2, chunk3 = chunk.partition("</think>")
                    chunk1 = chunk1.replace("\n", "\n-# ").replace("\n-# \n", "\n\n")
                    chunk = chunk1 + chunk2 + chunk3
                else:
                    chunk = chunk.replace("\n", "\n-# ").replace("\n-# \n", "\n\n")


            chunk_buf.append(chunk)
            chunk_len = len(chunk)
            chunk_buf_len += chunk_len
            msg_len += chunk_len
            response_len += chunk_len

            if chunk_buf_len >= 200:
                if msg_len >= 2000:
                    if was_thinking:
                        chunk_buf.insert(0, "-# ")
                    bot_msg = await message.channel.send("".join(chunk_buf))
                    msg_len = chunk_buf_len
                else:
                    bot_msg = await bot_msg.edit(content=bot_msg.content + "".join(chunk_buf))

                chunk_buf.clear()
                chunk_buf_len = 0

                if response_len >= max_response_len and max_response_len != 0:
                    await bot_msg.edit(content=bot_msg.content + "\n\nкароче я заебался писать иди нахуй")
                    break

        if chunk_buf:
            await bot_msg.edit(content=bot_msg.content + "".join(chunk_buf))


async def set_message_interval(message: Message) -> None:
    async with message.channel.typing():
        interval_str: str = message.content[22:].lower()
        
        if not interval_str.isnumeric() and interval_str != "random":
            await message.channel.send(f":prohibited: Неправильное значение интервала между сообщениями бота. Значение должно быть либо числом от `{bot_vars.SETTING_MESSAGE_INTERVAL_MIN}` до `{bot_vars.SETTING_MESSAGE_INTERVAL_MAX}`, либо `random`.")
            return

        if interval_str == "random":
            bot_vars.setting_message_interval_is_random = True
            bot_vars.message_interval_random = int(random.random() * 10) + 1

            await message.channel.send(f":white_check_mark: Интервал между сообщениями бота будет случайным для каждого сообщения.")
            return
        
        interval: int = int(interval_str)

        is_interval_less_than_min: bool = interval < bot_vars.SETTING_MESSAGE_INTERVAL_MIN
        is_interval_more_than_max: bool = interval > bot_vars.SETTING_MESSAGE_INTERVAL_MAX
        if is_interval_less_than_min or is_interval_more_than_max:
            await message.channel.send(f":prohibited: Интервал между сообщениями бота должен быть от `{bot_vars.SETTING_MESSAGE_INTERVAL_MIN}` до `{bot_vars.SETTING_MESSAGE_INTERVAL_MAX}` сообщений. Вы попытались установить: `{interval}`.")
            return

        bot_vars.setting_message_interval = interval
        bot_vars.setting_message_interval_is_random = False
        
        await message.channel.send(f":white_check_mark: Интервал между сообщениями бота установлен на `{bot_vars.setting_message_interval}` пользовательских сообщений.")


async def set_own_message_memory(message: Message) -> None:
    async with message.channel.typing():
        memory: int = int(message.content[24:])

        is_memory_less_than_min: bool = memory < bot_vars.SETTING_OWN_MESSAGE_MEMORY_MIN
        is_memory_more_than_max: bool = memory > bot_vars.SETTING_OWN_MESSAGE_MEMORY_MAX
        if is_memory_less_than_min or is_memory_more_than_max:
            await message.channel.send(f":prohibited: Память собственных сообщений бота должна быть от `{bot_vars.SETTING_OWN_MESSAGE_MEMORY_MIN}` до `{bot_vars.SETTING_OWN_MESSAGE_MEMORY_MAX}` сообщений. Вы попытались установить: `{memory}`.")
            return

        bot_vars.setting_own_message_memory = memory

        await message.channel.send(f":white_check_mark: Память собственных сообщений бота установлена на `{bot_vars.setting_own_message_memory}` сообщений.")


async def clear_memory(message: Message) -> None:
    async with message.channel.typing():
        bot_vars.recent_messages.clear()
        bot_vars.stylized_bot_messages.clear()
        await message.channel.send(f":white_check_mark: я всё заббыл нахуй")


async def stop_writing_here(message: Message) -> None:
    channel_id: int = message.channel.id

    if channel_id not in bot_vars.banned_automsg_channels:
        bot_vars.banned_automsg_channels.append(channel_id)
        await message.reply("извините я больше не буду сюда писать")
    else:
        bot_vars.banned_automsg_channels.remove(channel_id)
        await message.reply("ок я снова буду сюда писать")



async def status(message: Message) -> None:
    async with message.channel.typing():
        bot_status: str = f":coin: Ваши токены взаимодействия: `{bot_vars.user_interaction_tokens[message.author.id][0]}`"

        automsg_expansion: str | None = bot_vars.upgrades.get_automsg_expansion()
        if automsg_expansion is not None:
            bot_status += f"\n\n✍️ Пользовательский текст запроса сообщений инвалида:\n> {automsg_expansion}"

        if bot_vars.upgrades.is_fubar():
            bot_status += "\n\n👹 Я ебанутый."

        await message.channel.send(bot_status)


async def do_tamagotchi(message: Message) -> None:
    bot_vars.do_tamagotchi = not bot_vars.do_tamagotchi
    if bot_vars.do_tamagotchi:
        await message.reply(":white_check_mark: :white_check_mark: режим выживания вновь включён")
    else:
        await message.reply(":white_check_mark: режим выживания выключен..... НАВСЕГДА.......")


async def tokens(message: Message) -> None:
    async with message.channel.typing():
        tok_str_list: list[str] = message.content.split(maxsplit=1)

        if len(tok_str_list) != 2:
            await message.channel.send(f":coin: Ваши токены взаимодействия: `{bot_vars.user_interaction_tokens[message.author.id][0]}`")
            return

        tok_id_str: str = tok_str_list[1].removeprefix("<@").removesuffix(">")
        if tok_id_str.isnumeric():
            if int(tok_id_str) in bot_vars.user_interaction_tokens.keys():
                await message.channel.send(f":coin: Токены взаимодействия <@{tok_id_str}>: `{bot_vars.user_interaction_tokens[int(tok_id_str)][0]}`")
                return

        await message.channel.send(f":coin: Ваши токены взаимодействия: `{bot_vars.user_interaction_tokens[message.author.id][0]}`")


async def pay(message: Message) -> None:
    async with message.channel.typing():
        token_info: list[int] = bot_vars.user_interaction_tokens[message.author.id]

        pay_str_list: list[str] = message.content.split(maxsplit=2)
        if len(pay_str_list) < 3:
            await message.channel.send(f":prohibited: Укажите получателя и сумму перевода (у вас `{token_info[0]}` :coin:).")
            return
        
        recipient_id_str: str = pay_str_list[1].removeprefix("<@").removesuffix(">")
        payment_str: str = pay_str_list[2]
        recipient_id: int
        payment: int

        if payment_str.isnumeric() and recipient_id_str.isnumeric():
            payment = int(payment_str)
            recipient_id = int(recipient_id_str)
        elif payment_str == "all" and recipient_id_str.isnumeric():
            payment = token_info[0]
            recipient_id = int(recipient_id_str)
        else:
            await message.channel.send(f":prohibited: вы даун")
            return
        
        if payment < 1:
            await message.channel.send(f":prohibited: вы даун")
            return
        if payment > token_info[0]:
            await message.channel.send(f":prohibited: Недостаточно токенов (у вас `{token_info[0]}` :coin:).")
            return
        
        token_info[0] -= payment
        bot_vars.user_interaction_tokens[recipient_id][0] += payment

        await message.channel.send(f"Вы успешно перевели {payment} :coin: на счёт <@{recipient_id_str}>.")


async def upgrades(message: Message) -> None:
    async with message.channel.typing():
        upgrades_view: UpgradesView = UpgradesView(
            upgrades=bot_vars.upgrades,
            userid=message.author.id,
            user_token_info=bot_vars.user_interaction_tokens[message.author.id]
            )

        await message.channel.send(upgrades_view.to_str(), view=upgrades_view)


async def blackjack(message: Message) -> None:
    async with message.channel.typing():
        token_info: list[int] = bot_vars.user_interaction_tokens[message.author.id]

        bet_str_list: list[str] = message.content.split(maxsplit=1)
        if len(bet_str_list) < 2:
            await message.channel.send(f":prohibited: Укажите ставку (у вас `{token_info[0]}` :coin:).")
            return
        
        bet_str: str = bet_str_list[1]
        bet: int
        if bet_str.isnumeric():
            bet = int(bet_str)
        elif bet_str == "all":
            bet = token_info[0]
        else:
            await message.channel.send(f":prohibited: вы даун")
            return
        
        if bet < 1:
            await message.channel.send(f":prohibited: вы даун")
            return
        if bet > token_info[0]:
            await message.channel.send(f":prohibited: Недостаточно токенов (у вас `{token_info[0]}` :coin:).")
            return

        bj_manager: bj.GameManager = bj.GameManager(
            bet=bet,
            token_info=token_info,
            user=message.author
            )
        bj_view: bj.View = bj.View(bj_manager)
        await message.channel.send(str(bj_manager), view=bj_view)


async def slots(message: Message) -> None:
    async with message.channel.typing():
        token_info: list[int] = bot_vars.user_interaction_tokens[message.author.id]

        bet_str_list: list[str] = message.content.split(maxsplit=1)
        if len(bet_str_list) < 2:
            await message.channel.send(f":prohibited: Укажите ставку (у вас `{token_info[0]}` :coin:).")
            return
        
        bet_str: str = bet_str_list[1]
        bet: int
        if bet_str.isnumeric():
            bet = int(bet_str)
        elif bet_str == "all":
            bet = token_info[0]
        else:
            await message.channel.send(f":prohibited: вы даун")
            return
        
        if bet < 1:
            await message.channel.send(f":prohibited: вы даун")
            return
        if bet > token_info[0]:
            await message.channel.send(f":prohibited: Недостаточно токенов (у вас `{token_info[0]}` :coin:).")
            return

        slots_view: slot.View = slot.View(
            bet=bet,
            userid=message.author.id,
            token_info=token_info
        )

        msg: Message = await message.reply(str(slots_view), view=slots_view)
        await slots_view.set_msg_and_spin(msg)


async def leaderboard(message: Message) -> None:
    sorted_tok_info: list[set[int, list[int]]] = sorted(
        bot_vars.user_interaction_tokens.items(),
        key=lambda item: item[1][0],
        reverse=True
    )

    lb: str = ":bar_chart: Топ сервера по токенам:\n"

    for i, token_info in enumerate(sorted_tok_info):
        if i >= 5:
            break
        
        member_name: str
        try:
            member: Member = await message.guild.fetch_member(token_info[0])
            member_name = member.nick if member.nick is not None else member.name
        except NotFound as e:
            LOGGER.error(f"Can't fetch a member with id {token_info[0]} for ;leaderboard, fetching a user instead.")
            member_name = await bot_vars.client.fetch_user(token_info[0])

        lb += f"{i}. **{member_name}**: {token_info[1][0]} :coin:\n"

    lb += f"\nВаши токены: {bot_vars.user_interaction_tokens[message.author.id][0]} :coin:"

    await message.channel.send(lb)


async def translate(message: Message) -> None:
    async with message.channel.typing():
        args: list[str] = message.content.split(maxsplit=2)

        if len(args) != 3:
            if message.reference is None:
                await message.channel.send(":prohibited: вы даун")
                return

            if message.reference.cached_message is None:
                await message.channel.send("я не вижу сообщение! скопируй его в свою команду! сейчас же! сука!")
                return

            args.append(message.reference.cached_message.content)

        if "2" not in args[1]:
            await message.channel.send(":prohibited: вы даун")
            return

        lang_info: list[str] = args[1].split("2", maxsplit=1)
        if not lang_info[0]:
            lang_info[0] = "auto"

        available_langs: list[str] = [
            "ar", "az", "bg", "bn", "ca", "cs", "da", "de", "el", "en", "eo",
            "es", "et", "fa", "fi", "fr", "ga", "he", "hi", "hu", "id", "it",
            "ja", "ko", "lt", "lv", "ms", "nb", "nl", "pl", "pt", "ro", "ru",
            "sk", "sl", "sq", "sr", "sv", "th", "tl", "tr", "uk", "zh", "zt",
            "auto"
        ]

        for lang in lang_info:
            if lang not in available_langs:
                await message.reply(f"нет такого языка \"{lang}\"")
                return

        url: str = "https://translate.disroot.org/translate"
        data: dict = {
            "q": args[2],
            "source": lang_info[0],
            "target": lang_info[1],
            "format": "text",
            "alternatives": 3
        }

        response: requests.Response = requests.post(url, json=data)
        response_json: dict = response.json()

        match response.status_code:
            case 200:
                bot_reply: str = response_json["translatedText"]
 
                if response_json["alternatives"]:
                    bot_reply += "\n\nАльтернативные версии перевода:"
                    for alt in response_json["alternatives"]:
                        bot_reply += f"\n- {alt}"

                await message.reply(bot_reply)
            case 400 | 403:
                await message.reply(":prohibited: ашипка ноль ноль ноль")
                LOGGER.error(f"Error while trying to translate a message ({message.content}): {response_json['error']}")
            case 429:
                await message.reply(":warning: ах ах слишком быстро")
                LOGGER.error(f"Error while trying to translate a message ({message.content}): {response_json['error']}")
            case 500:
                await message.reply(":question: ошибка переводчика")
                LOGGER.error(f"Error while trying to translate a message ({message.content}): {response_json['error']}")


async def help(message: Message) -> None:
    help_msg: str = "## 🤖 Общение с ботом 🤖\n"
    help_msg += "- `;set-message-interval [Интервал: int | \"random\"]` - поставить количество пользовательских сообщений, после которых бот сам что-то напишет.\n"
    help_msg += "- `;set-own-message-memory [Память: int]` - поставить количество собственных сообщений бота, которые он запомнит и учтёт при написании следующего своего сообщения.\n"
    help_msg += "- `;clear-memory` - Очищает память бота от своих и пользовательских сообщений.\n"
    # TODO: shorten ;help
    # help_msg += "- `;stop-writing-here (;stop)` - Запрещает инвалиду автоматически писать в данный чат, но не запрещает пользоваться командами.\n"
    help_msg += "## 💸 Экономика 💸\n"
    help_msg += "- `;tokens (;tok) [@Ник - mention | None]` - Показывает ваши токены (либо токены указанного человека).\n"
    help_msg += "- `;pay [@Ник - mention, Сумма - int | \"all\"]` - Переводит токены с вашего счета на чужой.\n"
    help_msg += "- `;leaderboard (;top, ;lb)` - Показать топ сервера по токенам.\n"
    help_msg += "- `;upgrade (;upgrades)` - Открывает меню апгрейдов.\n"
    help_msg += "- `;blackjack (;bj) [Ставка: int | \"all\"]` - Сыграть в блэкджек.\n"
    help_msg += "- `;tax` - Заплатить налог. \n"
    help_msg += "## 🧼 Уход за ботом был убран по понятным причинам.🧼\n"
    help_msg += "- `;status` - Показывает состояние бота и количество ваших токенов.\n"
    help_msg += "## 🔧 Утилиты 🔧\n"
    help_msg += "- `;prompt [Сообщение: str]` - обратиться к Arcee Trinity Mini.\n"
    help_msg += "- `;translate (;tl) [Языки: str, Сообщение: str]` - перевести текст. Языки перевода должны иметь следующий вид: `{ЯзыкОригинала}2{ЯзыкПеревода}` (прим. "
    help_msg += "`;tl en2ru text text` переведёт указанный английский текст на русский язык). Можно оставить язык оригинала пустым для его автоматического определения "
    help_msg += "(прим. `;tl 2ru text text`). Можно ответить на чужое сообщение, чтобы перевести его (прим. `;tl 2zh` переведёт чужое сообщение на китайский).\n"
    help_msg += "- `;coinflip (;cf)` - подбросить монетку.\n"
    help_msg += "- `;ping` - pong.\n"
    help_msg += "- `;resurrect` - Убить инвалида. Некромантия его воскресит и он отвиснет. \n"

    await message.channel.send(help_msg)


async def process_tokens_info(message: Message) -> None:
    userid: int = message.author.id

    if userid not in bot_vars.user_interaction_tokens:
            bot_vars.user_interaction_tokens[userid] = [3, 5, int(time.time())]

    if message.author.bot:
        return

    if bot_vars.user_interaction_tokens[userid][1] <= 0:
        bot_vars.user_interaction_tokens[userid][1] = 5
        bot_vars.user_interaction_tokens[userid][0] += 1
        await message.add_reaction("🪙")
    else:
        bot_vars.user_interaction_tokens[userid][1] -= 1

    time_since_last_message: int = int(time.time()) - bot_vars.user_interaction_tokens[userid][2]
    if time_since_last_message >= 3600:
        max_afk_hours: int = bot_vars.upgrades.get_max_afk_hours(message.author.id)
        bot_vars.user_interaction_tokens[userid][0] += min(max_afk_hours, time_since_last_message // 3600)
        await message.add_reaction("🪙")
    
    bot_vars.user_interaction_tokens[userid][2] = int(time.time())


async def automessage(message: Message) -> None:
    if message.channel.id in bot_vars.banned_automsg_channels:
        return

    bot_vars.recent_messages.append(message)

    is_mentioned: bool = bot_vars.client.user in message.mentions

    regex_match = re.search(r"(?:\s|^)инвалид", message.content.lower())
    is_mentioned_directly: bool = regex_match is not None
    
    is_time_to_automessage: bool

    if bot_vars.setting_message_interval_is_random:
        is_time_to_automessage = bot_vars.message_interval_random <= 0
        if is_time_to_automessage:
            bot_vars.message_interval_random = int(random.random() * 10.0) + 4
        else:
            bot_vars.message_interval_random -= 1
    else:
        recent_messages_len: int = len(bot_vars.recent_messages)
        is_time_to_automessage = recent_messages_len >= bot_vars.setting_message_interval

    automessage_condition: bool = is_mentioned or is_mentioned_directly or is_time_to_automessage
    if automessage_condition and bot_vars.recent_messages:
        async with message.channel.typing():
            automessage: str = await ai.generate_automessage(bot_vars.ai_key, bot_vars)
            await message.channel.send(automessage)

            bot_vars.recent_messages.clear()

            bot_vars.stylized_bot_messages.append(automessage)
            while (len(bot_vars.stylized_bot_messages) > bot_vars.setting_own_message_memory):
                bot_vars.stylized_bot_messages.pop(0)


async def check_if_waiting_for_message(message: Message) -> None:
    if bot_vars.upgrades.is_automsg_expansion_being_bought_by_user(message.author.id):
        bot_vars.upgrades.set_automsg_expansion(message.content)
        await message.reply(":white_check_mark: Текст запроса сообщений успешно обновлён.")
