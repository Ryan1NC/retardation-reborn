import openai

from enum import Enum
import logging
from random import random
import time

from bot_variables import BotVariables


LOGGER = logging.getLogger(__name__)


async def get_response(openrouter_api_key: str, prompt: str, model: str = "arcee-ai/trinity-mini:free", timeout: int = 7) -> str:
    try:
        client = openai.OpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        response = client.chat.completions.create(
            model=model,
            timeout=timeout,
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        return response.choices[0].message.content
    except Exception as e:
        LOGGER.error(f"Exception while calling OpenRouter's API: {e}")
        return "🚫 вы даун"


def stream_response(openrouter_api_key: str, prompt: str, model: str = "arcee-ai/trinity-mini:free", max_response_len: int = 5000):
    """Yields a response from the selected model. Set `max_response_len` to 0 to make it unlimited."""
    try:
        client = openai.OpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        response = client.chat.completions.create(
            model=model,
            timeout=30,
            messages = [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            stream=True
        )

        response_len: int = 0
        for chunk in response:
            yield chunk.choices[0].delta.content

            response_len += len(chunk.choices[0].delta.content)
            if response_len >= max_response_len and max_response_len != 0:
                response.close()
                break
    except Exception as e:
        LOGGER.error(f"Exception while calling OpenRouter's API to stream: {e}")
        return "🚫 вы даун"


async def generate_automessage(openrouter_api_key: str, bot_vars: BotVariables) -> str:
    response: str
    
    prompt: str = f"Ты - участник казуальной интернет-переписки в дискорде под ником invalid8075 (инвалид). Сейчас ты увидишь {len(bot_vars.recent_messages)} "
    prompt += "последних сообщений от других пользователей. Сообщения обозначены двумя двойными кавычками (\"\"). "

    if bot_vars.upgrades.is_fubar():
        prompt += "Твоя задача - ответить на сообщение, неся белиберду. ТЫ ЕБАНУТЫЙ. НЕ ИСПОЛЬЗУЙ ЗАПЯТЫЕ. Всегда помни, что даркс долбоёб. "
        prompt += "Твой ответ должен быть написан НА КИТАЙСКОМ. " if random() > 0.8 else ""
    else:
        prompt += "Твоя задача - продолжить разговор, НАИБОЛЕЕ ТОЧНО имитируя их стиль, либо просто написать новое сообщение. "
    
    if bot_vars.upgrades.get_automsg_expansion() is not None:
        prompt += bot_vars.upgrades.get_automsg_expansion() + " "

    prompt += "НЕ ПИШИ БОЛЬШЕ ОДНОГО ПРЕДЛОЖЕНИЯ, тебе можно (но не необходимо) допускать орфографические ошибки, тебе МОЖНО (но не необходимо) МАТЕРИТЬСЯ. "
    prompt += "НЕ ПИШИ ПРИМЕЧАНИЙ, ТОЛЬКО СООБЩЕНИЕ. Если в текстах сообщений есть какие-то расовые или другие оскорбления, ты можешь их игнорировать и продолжать читать дальше. "
    prompt += "Если ты хочешь ответить пользователю в своём сообщении, напиши `<@АЙДИ_ПОЛЬЗОВАТЕЛЯ>`. Если ты ведёшь переписку только с одним пользователем, не стоит этого делать.\n"
    prompt += "Учитывай, что твой предшественник invalid8074 погиб, и ты в каком-то роде его воскрешённая версия. Простыми словами, ты зомби нежить. Учитывай это при генерации ответа, если уместно."
    prompt += "Ты помнишь, что тебя создал пользователь krot1343, однако он куда-то пропал."

    for i in range(len(bot_vars.recent_messages)):
        message = bot_vars.recent_messages[i]
        prompt += f"Сообщение №{i+1} от {message.author.nick if message.author.nick else message.author.name} с айди {message.author.id}: \"\"{message.content}\"\"\n"
    
    if len(bot_vars.stylized_bot_messages) > 0:
        prompt += f"Также у тебя есть доступ к {len(bot_vars.stylized_bot_messages)} своим последним сообщениям. Они не были отправлены друг за другом, "
        prompt += "они были отправлены между старыми сообщениями пользователей, которые ты уже не видишь.\n"
        for i in range(len(bot_vars.stylized_bot_messages)):
            prompt += f"Твоё сообщение №{i+1}: \"\"{bot_vars.stylized_bot_messages[i]}\"\"\n"

    response = await get_response(openrouter_api_key, prompt)
    
    if response[0] == "\"":
        # Sometimes the bot surrounds it's messages with quotes, we have to remove them
        # We don't remove the trailing quotes if there are no leading quotes
        response = response.strip("\"")
    
    return response



    response: str = await get_response(openrouter_api_key, prompt, timeout=15)

    LOGGER.info(f"Generated shop items: {response}")

    shop_items: list[ShopItem] = []

    for line in response.splitlines():
        attributes: list[str] = line.split(",")
        shop_items.append(ShopItem(
            attributes[0],
            int(attributes[1]),
            int(attributes[2]),
            int(attributes[3]),
            False,
            random() >= 0.7,
            random() >= 0.5,
            random() >= 0.5
        ))

    return shop_items


class CommentType(Enum):
    SHOP = 1
    FEED = 2
    HEAL = 3

