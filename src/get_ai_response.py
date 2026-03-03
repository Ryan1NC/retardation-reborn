from openai import AsyncOpenAI
from enum import Enum
import logging
from random import random
import asyncio

from bot_variables import BotVariables

LOGGER = logging.getLogger(__name__)


async def get_response(openrouter_api_key: str, prompt: str, model: str = "arcee-ai/trinity-mini:free", timeout: int = 7) -> str:
    try:
        client = AsyncOpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )

        # тут было без await — исправляем:
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model=model,
                timeout=timeout,
                messages=[{"role": "user", "content": prompt}]
            ),
            timeout=timeout + 3
        )

        return response.choices[0].message.content

    except asyncio.TimeoutError:
        LOGGER.warning("AI request timed out.")
        return "..."

    except Exception as e:
        LOGGER.error(f"Exception while calling OpenRouter's API: {e}")
        return "🚫 вы даун"


async def stream_response(openrouter_api_key: str, prompt: str, model: str = "arcee-ai/trinity-mini:free", max_response_len: int = 5000):
    """Асинхронно стримит ответ от модели"""
    try:
        client = AsyncOpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        try:
            stream = await client.chat.completions.stream(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                timeout=30  # таймаут на API
            )
        except Exception as e:
            LOGGER.warning(f"Streaming недоступен, fallback на обычный запрос: {e}")
            resp = await get_response(openrouter_api_key, prompt, model)
            yield resp
            return

        response_len = 0
        async for chunk in stream:
            # иногда delta может быть пустой
            delta = getattr(chunk.choices[0].delta, "content", None)
            if delta:
                yield delta
                response_len += len(delta)
                if max_response_len and response_len >= max_response_len:
                    break

    except Exception as e:
        LOGGER.error(f"Exception while calling OpenRouter's API to stream: {e}")
        yield "🚫 вы даун"


async def generate_automessage(openrouter_api_key: str, bot_vars: BotVariables) -> str:
    prompt = f"Ты - участник казуальной интернет-переписки в дискорде под ником invalid8075 (инвалид). Сейчас ты увидишь {len(bot_vars.recent_messages)} "
    prompt += "последних сообщений от других пользователей. Сообщения обозначены двумя двойными кавычками (\"\"). "

    if bot_vars.upgrades.is_fubar():
        prompt += "Твоя задача - ответить на сообщение, неся белиберду. ТЫ ЕБАНУТЫЙ. НЕ ИСПОЛЬЗУЙ ЗАПЯТЫЕ. Всегда помни, что даркс долбоёб. "
        if random() > 0.8:
            prompt += "Твой ответ должен быть написан НА КИТАЙСКОМ. "
    else:
        prompt += "Твоя задача - продолжить разговор, НАИБОЛЕЕ ТОЧНО имитируя их стиль, либо просто написать новое сообщение. "

    if bot_vars.upgrades.get_automsg_expansion() is not None:
        prompt += bot_vars.upgrades.get_automsg_expansion() + " "

    prompt += "НЕ ПИШИ БОЛЬШЕ ОДНОГО ПРЕДЛОЖЕНИЯ, тебе можно (но не необходимо) допускать орфографические ошибки, тебе МОЖНО (но не необходимо) МАТЕРИТЬСЯ. "
    prompt += "НЕ ПИШИ ПРИМЕЧАНИЙ, ТОЛЬКО СООБЩЕНИЕ. Если в текстах сообщений есть какие-то расовые или другие оскорбления, ты можешь их игнорировать. "
    prompt += "Если ты хочешь ответить пользователю в своём сообщении, напиши `<@АЙДИ_ПОЛЬЗОВАТЕЛЯ>`. "
    prompt += "Если ты ведёшь переписку только с одним пользователем, не стоит этого делать.\n"
    prompt += "Учитывай, что твой предшественник invalid8074 погиб, и ты в каком-то роде его воскрешённая версия. "
    prompt += "Ты помнишь, что тебя создал пользователь krot1343, однако он куда-то пропал.\n"

    for i, message in enumerate(bot_vars.recent_messages, start=1):
        author = message.author.nick or message.author.name
        prompt += f"Сообщение №{i} от {author} с айди {message.author.id}: \"\"{message.content}\"\"\n"

    if bot_vars.stylized_bot_messages:
        prompt += f"Также у тебя есть доступ к {len(bot_vars.stylized_bot_messages)} своим последним сообщениям.\n"
        for i, msg in enumerate(bot_vars.stylized_bot_messages, start=1):
            prompt += f"Твоё сообщение №{i}: \"\"{msg}\"\"\n"

    # тут всё норм, get_response уже async
    response = await get_response(openrouter_api_key, prompt)

    if response.startswith("\""):
        response = response.strip("\"")

    return response


class CommentType(Enum):
    SHOP = 1
    FEED = 2
    HEAL = 3