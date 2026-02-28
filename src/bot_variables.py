from discord import Message, Client

import csv, json
from dataclasses import asdict, dataclass, field, fields
import os
import time

from upgrades import Upgrades
import requests


@dataclass
class BotVariables:
    CREATED_AT: int = int(time.time())
    
    ai_key: str = None
    client: Client = None

    SETTING_MESSAGE_INTERVAL_MIN: int = 1
    SETTING_MESSAGE_INTERVAL_MAX: int = 50
    setting_message_interval: int = 7
    setting_message_interval_is_random: bool = True
    message_interval_random: int = 4

    SETTING_OWN_MESSAGE_MEMORY_MIN: int = 1
    SETTING_OWN_MESSAGE_MEMORY_MAX: int = 10
    setting_own_message_memory: int = 3

    recent_messages: list[Message] = field(default_factory=list[Message])
    stylized_bot_messages: list[str] = field(default_factory=list[str])

    banned_automsg_channels: list[int] = field(default_factory=list[int])


    user_interaction_tokens: dict[int, list[int]] = field(default_factory=dict[int, list[int]])  # key - userid;
                                                                                                 # list[0] - tokens;
                                                                                                 # list[1] - messages until next token

    upgrades: Upgrades = Upgrades()


    def generate_dto(self) -> "_BotVariablesDto":
        return _BotVariablesDto(
            self.CREATED_AT,
            self.SETTING_MESSAGE_INTERVAL_MIN,
            self.SETTING_MESSAGE_INTERVAL_MAX,
            self.setting_message_interval,
            self.setting_message_interval_is_random,
            self.message_interval_random,
            self.SETTING_OWN_MESSAGE_MEMORY_MIN,
            self.SETTING_OWN_MESSAGE_MEMORY_MAX,
            self.setting_own_message_memory,
            self.banned_automsg_channels,
            self.user_interaction_tokens.copy(),
            self.upgrades.upgrades[2].levels.copy()
        )
    
    @classmethod
    def from_file(cls, readpath: str) -> "BotVariables":
        try:
            with open(readpath, "r") as file:
                reader = csv.DictReader(file)
                reader.line_num
                for row in reader:
                    upgrades: Upgrades = Upgrades().reinstantiate(
                        afk_token_levels = eval(row.get("afk_token_levels", "{}"))
                    )

                    bot_vars = cls(
                        CREATED_AT                     = int(row.get("CREATED_AT", int(time.time()))),
                        SETTING_MESSAGE_INTERVAL_MIN   = int(row["SETTING_MESSAGE_INTERVAL_MIN"]),
                        SETTING_MESSAGE_INTERVAL_MAX   = int(row["SETTING_MESSAGE_INTERVAL_MAX"]),
                        setting_message_interval       = int(row["setting_message_interval"]),
                        setting_message_interval_is_random = (
                            row["setting_message_interval_is_random"] == "True"
                        ),
                        message_interval_random        = int(row["message_interval_random"]),
                        SETTING_OWN_MESSAGE_MEMORY_MIN = int(row["SETTING_OWN_MESSAGE_MEMORY_MIN"]),
                        SETTING_OWN_MESSAGE_MEMORY_MAX = int(row["SETTING_OWN_MESSAGE_MEMORY_MAX"]),
                        setting_own_message_memory     = int(row["setting_own_message_memory"]),
                        banned_automsg_channels        = eval(row.get("banned_automsg_channels", "[]")),
                        user_interaction_tokens        = eval(row["user_interaction_tokens"]),
                        upgrades                       = upgrades
                    )
            return bot_vars
        except Exception as e:
            raise e
    
    def write_to_file(self, writepath: str) -> None:
        dir_path = os.path.dirname(writepath)

        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        
        bot_vars_dto: _BotVariablesDto = self.generate_dto()
        
        try:
            with open(writepath, "w+") as file:
                flds = [fld.name for fld in fields(_BotVariablesDto)]
                writer = csv.DictWriter(file, flds)

                writer.writeheader()
                writer.writerow(asdict(bot_vars_dto))
        except Exception as e:
            raise e


@dataclass
class _BotVariablesDto:
    CREATED_AT: int

    SETTING_MESSAGE_INTERVAL_MIN: int
    SETTING_MESSAGE_INTERVAL_MAX: int
    setting_message_interval: int
    setting_message_interval_is_random: bool
    message_interval_random: int

    SETTING_OWN_MESSAGE_MEMORY_MIN: int
    SETTING_OWN_MESSAGE_MEMORY_MAX: int
    setting_own_message_memory: int

    banned_automsg_channels: list[int]

    user_interaction_tokens: dict[int, list[int]]

    afk_token_levels: dict[int, int]
