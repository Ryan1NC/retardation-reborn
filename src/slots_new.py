from unittest import case

import discord
import asyncio
from enum import Enum
import random

_REEL_EMOJIS: tuple = (
    ":skull:", "<:proverka:1307010119824965723>", ":cherries:", ":mushroom:",
    "<:gragas:1336062411970580511>", "<:esq_gragas:1336062410041196646>",
    "<:bulborb:1336061550498287616>", "<:nuclear_bulborb:1336061387847372830>",
    ":star:", ":egg:", "<a:slots:1477624553428488304>"
)

_PIROTS_WEIGHTS_NEW: tuple = (46, 48, 52, 54, 4, 2, 1, 2, 2, 1)

_PIROTS_NEW_EMOJIS: tuple = (
    "<:High1:1410726957259161793>", "<:High2:1408765844296826990>", "<:High3:1410726975454056488>", "<:High4:1410726991644065842>", ":red_circle:",
    ":purple_circle:", ":green_circle:", ":blue_circle:", ":red_circle:",
    ":purple_circle:", ":green_circle:", ":blue_circle:", ":black_large_square:", ":one:", ":two:", ":three:",
    ":one:", ":two:", ":three:",
    ":negative_squared_cross_mark:", ":sparkle:", ":eight_spoked_asterisk:",
    ":negative_squared_cross_mark:", ":sparkle:", ":eight_spoked_asterisk:"
)

_PIROTS_WIN: list[str] = [
    "https://media.discordapp.net/attachments/1353855676853518389/1479183692147720335/image.png",  # mega win
    "https://media.discordapp.net/attachments/1353855676853518389/1479183895789572106/image.png",  # gold rush
    "https://media.discordapp.net/attachments/1353855676853518389/1479184083316773126/image.png",  # epic win
    "https://media.discordapp.net/attachments/1353855676853518389/1479184222924308551/image.png"   # super win
]

class DummyMessage:
    async def edit(self, *args, **kwargs):
        pass

SIMULATION = True

class _Reel(Enum):
    SKULL = 1
    PROVERKA = 2
    CHERRIES = 3
    FUNGUS = 4
    GRAGAS = 5
    ESQ_GRAGAS = 6
    BULBORB = 7
    NUCLEAR_BULBORB = 8
    STAR = 9
    EGG = 10
    SPINNING = 11

    def to_emoji(self) -> str:
        return _REEL_EMOJIS[self.value - 1]

    @classmethod
    def get_random(cls) -> "_Reel":
        return cls(random.sample(
            population=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            k=1,
            counts=[17, 33, 10, 10, 15, 9, 5, 1, 37, 37]
        )[0])


class _Pirots_NEW(Enum):
    # Птицы (охотники)
    RED_BIRD = 1
    PURPLE_BIRD = 2
    GREEN_BIRD = 3
    BLUE_BIRD = 4
    # Самоцветы (еда)
    RED_GEM = 5
    PURPLE_GEM = 6
    GREEN_GEM = 7
    BLUE_GEM = 8
    # Съеденные самоцветы
    RED_GEM_CLAIMED = 9
    PURPLE_GEM_CLAIMED = 10
    GREEN_GEM_CLAIMED = 11
    BLUE_GEM_CLAIMED = 12
    EMPTY = 13  # пустая клетка
    #Съеденные апгрейды
    UPGRADE_LV_1 = 14
    UPGRADE_LV_2 = 15
    UPGRADE_LV_3 = 16
    #Съеденные апгрейды
    UPGRADE_LV_1_CLAIMED = 17
    UPGRADE_LV_2_CLAIMED = 18
    UPGRADE_LV_3_CLAIMED = 19
    #Универсальные апгрейды
    UN_UPGRADE_LV_1 = 20
    UN_UPGRADE_LV_2 = 21
    UN_UPGRADE_LV_3 = 22
    #Съеденные универсальные апгрейды
    UN_UPGRADE_LV_1_CLAIMED = 23
    UN_UPGRADE_LV_2_CLAIMED = 24
    UN_UPGRADE_LV_3_CLAIMED = 25

    def to_emoji(self) -> str:
        """Возвращает визуальный символ."""
        return _PIROTS_NEW_EMOJIS[self.value - 1]

    @classmethod
    def get_random_gem(cls) -> "_Pirots_NEW":
        """Случайный выбор самоцвета с заданными шансами."""
        return cls(random.sample(
            population=[5, 6, 7, 8, 14, 15, 16, 20, 21, 22],
            k=1,
            counts=[138, 144, 156, 162, 6, 5, 4, 4, 2, 1]
        )[0])

    @classmethod
    def get_random_board(cls) -> list[list["_Pirots_NEW"]]:
        random_gems = random.choices(
            population=[cls.RED_GEM, cls.PURPLE_GEM, cls.GREEN_GEM, cls.BLUE_GEM, cls.UPGRADE_LV_1, cls.UPGRADE_LV_2,
                        cls.UPGRADE_LV_3, cls.UN_UPGRADE_LV_1, cls.UN_UPGRADE_LV_2, cls.UN_UPGRADE_LV_3],
            weights=_PIROTS_WEIGHTS_NEW,
            k=36
        )

        random_board = [[random_gems[x * 5 + y] for x in range(6)] for y in range(6)]

        birds_pos = [(x, y) for x in range(6) for y in range(6)]
        random.shuffle(birds_pos)

        random_board[birds_pos[0][0]][birds_pos[0][1]] = _Pirots_NEW.RED_BIRD
        random_board[birds_pos[1][0]][birds_pos[1][1]] = _Pirots_NEW.PURPLE_BIRD
        random_board[birds_pos[2][0]][birds_pos[2][1]] = _Pirots_NEW.GREEN_BIRD
        random_board[birds_pos[3][0]][birds_pos[3][1]] = _Pirots_NEW.BLUE_BIRD

        return random_board


# ---------- Основная логика бонусной мини-игры ----------
class View_pirots(discord.ui.View):
    """UI-класс для мини-игры 'Pirots' (птички и самоцветы)."""

    bet: int
    player_userid: int
    player_token_info: list[int]
    msg: discord.Message
    reels: list[list[_Pirots_NEW]]

    def __init__(self, bet: int, userid: int, token_info: list[int], rows: int = 6, cols: int = 6):
        """Создаёт игровое поле и инициализирует состояние игрока."""
        super().__init__(timeout=30)
        self.bet = bet
        self.player_userid: int = userid
        self.player_token_info = token_info
        #уровни прокачки гемчиков
        self.red_lvl: int = 1
        self.purple_lvl: int = 1
        self.green_lvl: int = 1
        self.blue_lvl: int = 1

        # игровое поле (пока пустое)
        self.pirots_reels = [[_Reel.SPINNING for _ in range(cols)] for _ in range(rows)]

        # показатели выигрыша
        self.winnings = 0.0
        self.pirots_winnings = 0.0
        #self.total_winnings = 0.0

        # флаги состояний
        self.is_bonus = False
        self.is_coin_game = False
        self.is_spinning = True

        # сохранённые бонусы (если были)
        self.saved_bonus_spins = 0
        self.saved_bonus_winnings = 0.0

        # списание ставки
        self.player_token_info[0] -= self.bet


    def get_embed(self) -> discord.Embed:
        """Возвращает Embed с текущим состоянием поля и картинкой выигрыша."""
        winnings = max(self.winnings, self.pirots_winnings)

        embed = discord.Embed(
            title=f"<@{self.player_userid}> | :coin: Ставка: {self.bet}",
            description="\n".join(
                "> " + "".join(cell.to_emoji() for cell in row) for row in self.pirots_reels
            )
        )

        embed.add_field(
            name="Множители птиц",
            value=(
                f"<:High1:1410726957259161793> {self.red_lvl} | "
                f"<:High2:1408765844296826990> {self.purple_lvl} | "
                f"<:High3:1410726975454056488> {self.green_lvl} | "
                f"<:High4:1410726991644065842> {self.blue_lvl}"
            ),
            inline=False
        )

        if self.is_spinning:
            embed.add_field(name="Навар", value=f"+{int(winnings)} :coin:", inline=False)
        else:
            embed.add_field(name="Игра закончена", value=f"Вы наварились на {int(winnings)} :coin:", inline=False)


            def get_win(winnings, bet) -> int | None:
                ratio = winnings / bet
                if ratio >= 50:  # mega win
                    return 0
                elif ratio >= 20:  # gold win
                    return 1
                elif ratio >= 10:  # epic win
                    return 2
                elif ratio >= 5:  # super win
                    return 3
                else:
                    return None

            win_index = get_win(winnings, self.bet)
            if win_index is not None:
                embed.set_image(url=_PIROTS_WIN[win_index])

        return embed


    # -------- Игровая логика --------

    async def pirots_reset_board(self) -> None:
        #new_board = _Pirots_NEW.get_random_board()
        """Создаёт новое поле и расставляет птиц и самоцветы."""
        n_rows = len(self.pirots_reels)
        n_cols = len(self.pirots_reels[0])

        # Пустое поле
        new_board = [[_Pirots_NEW.EMPTY for _ in range(n_cols)] for _ in range(n_rows)]

        # случайные позиции для птиц
        positions = [(r, c) for r in range(n_rows) for c in range(n_cols)]
        random.shuffle(positions)

        # размещаем 4 птицы
        new_board[positions[0][0]][positions[0][1]] = _Pirots_NEW.RED_BIRD
        new_board[positions[1][0]][positions[1][1]] = _Pirots_NEW.PURPLE_BIRD
        new_board[positions[2][0]][positions[2][1]] = _Pirots_NEW.GREEN_BIRD
        new_board[positions[3][0]][positions[3][1]] = _Pirots_NEW.BLUE_BIRD

        # заполняем остальное самоцветами
        for r in range(n_rows):
            for c in range(n_cols):
                if new_board[r][c] is _Pirots_NEW.EMPTY:
                    new_board[r][c] = _Pirots_NEW.get_random_gem()

        # Анимация: открываем поле по столбцам
        self.pirots_reels = [[_Pirots_NEW.EMPTY for _ in range(n_cols)] for _ in range(n_rows)]
        for c in range(n_cols):
            await self.msg.edit(embed=self.get_embed(), view=self)
            if not SIMULATION:
                await asyncio.sleep(0.35)
            for r in range(n_rows):
                self.pirots_reels[r][c] = new_board[r][c]

    async def pirots_move_birds(self) -> None:
        """Основной цикл движения птиц и 'поедания' самоцветов."""
        moved: bool = False
        n_rows = len(self.pirots_reels)
        n_cols = len(self.pirots_reels[0])

        for c in range(n_cols):
            for r in range(n_rows):
                cell: _Pirots_NEW = self.pirots_reels[r][c]
                if cell in [_Pirots_NEW.RED_BIRD, _Pirots_NEW.PURPLE_BIRD, _Pirots_NEW.GREEN_BIRD,
                            _Pirots_NEW.BLUE_BIRD]:
                    # Список всех допустимых самоцветов для этой птицы
                    target_gems = [
                        _Pirots_NEW(cell.value + 4),
                        _Pirots_NEW(14),
                        _Pirots_NEW(15),
                        _Pirots_NEW(16),
                        _Pirots_NEW(20),
                        _Pirots_NEW(21),
                        _Pirots_NEW(22)
                    ]

                    cluster: list[tuple[int, int]] = self.pirots_map_gem_cluster(
                        target_gems=target_gems,
                        bird_position=(r, c),
                        cluster=list()
                    )

                    # Перемещаем птицу по кластеру
                    for i in range(1, len(cluster)):
                        gem_r, gem_c = cluster[i]
                        prev_r, prev_c = cluster[i - 1]
                        target_cell = self.pirots_reels[gem_r][gem_c]

                        # проверяем на множитель
                        if target_cell in (_Pirots_NEW.UPGRADE_LV_1_CLAIMED,
                                           _Pirots_NEW.UPGRADE_LV_2_CLAIMED,
                                           _Pirots_NEW.UPGRADE_LV_3_CLAIMED,
                                           _Pirots_NEW.UN_UPGRADE_LV_1_CLAIMED,
                                           _Pirots_NEW.UN_UPGRADE_LV_2_CLAIMED,
                                           _Pirots_NEW.UN_UPGRADE_LV_3_CLAIMED):
                            # начисляем множитель, но не затираем апгрейд
                            match cell:
                                case _Pirots_NEW.RED_BIRD:
                                    if target_cell == _Pirots_NEW.UPGRADE_LV_1_CLAIMED:
                                        self.red_lvl += 1
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_2_CLAIMED:
                                        self.red_lvl += 2
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_3_CLAIMED:
                                        self.red_lvl += 3
                                case _Pirots_NEW.PURPLE_BIRD:
                                    if target_cell == _Pirots_NEW.UPGRADE_LV_1_CLAIMED:
                                        self.purple_lvl += 1
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_2_CLAIMED:
                                        self.purple_lvl += 2
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_3_CLAIMED:
                                        self.purple_lvl += 3
                                case _Pirots_NEW.GREEN_BIRD:
                                    if target_cell == _Pirots_NEW.UPGRADE_LV_1_CLAIMED:
                                        self.green_lvl += 1
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_2_CLAIMED:
                                        self.green_lvl += 2
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_3_CLAIMED:
                                        self.green_lvl += 3
                                case _Pirots_NEW.BLUE_BIRD:
                                    if target_cell == _Pirots_NEW.UPGRADE_LV_1_CLAIMED:
                                        self.blue_lvl += 1
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_2_CLAIMED:
                                        self.blue_lvl += 2
                                    elif target_cell == _Pirots_NEW.UPGRADE_LV_3_CLAIMED:
                                        self.blue_lvl += 3

                            #универсальные апгрейды:
                            if target_cell == _Pirots_NEW.UN_UPGRADE_LV_1_CLAIMED:
                                self.red_lvl += 1
                                self.purple_lvl += 1
                                self.green_lvl += 1
                                self.blue_lvl += 1
                            elif target_cell == _Pirots_NEW.UN_UPGRADE_LV_2_CLAIMED:
                                self.red_lvl += 2
                                self.purple_lvl += 2
                                self.green_lvl += 2
                                self.blue_lvl += 2
                            elif target_cell == _Pirots_NEW.UN_UPGRADE_LV_3_CLAIMED:
                                self.red_lvl += 3
                                self.purple_lvl += 3
                                self.green_lvl += 3
                                self.blue_lvl += 3

                            # проверки, не зашёл ли икс за лимит в 7
                            if self.red_lvl > 7:
                                self.red_lvl = 7
                            if self.purple_lvl > 7:
                                self.purple_lvl = 7
                            if self.green_lvl > 7:
                                self.green_lvl = 7
                            if self.blue_lvl > 7:
                                self.blue_lvl = 7

                            # очистка клетки после срабатывания
                            self.pirots_reels[gem_r][gem_c] = cell
                            self.pirots_reels[prev_r][prev_c] = _Pirots_NEW.EMPTY

                        # теперь, если это не множитель, просто двигаем птицу
                        else:
                            self.pirots_reels[gem_r][gem_c] = cell
                            self.pirots_reels[prev_r][prev_c] = _Pirots_NEW.EMPTY
                        self.pirots_reels[prev_r][prev_c] = _Pirots_NEW.EMPTY

                        #print("DEBUG:", target_cell, target_cell.value, cluster)
                        # начисление выигрыша за поедание
                        #self.total_winnings += self.bet * 0.1
                        #self.pirots_winnings += self.bet * (0.1)
                        if target_cell.value <= 13:
                            match cell:
                                case _Pirots_NEW.RED_BIRD:
                                    self.pirots_winnings += self.bet * 0.1 * self.red_lvl
                                case _Pirots_NEW.PURPLE_BIRD:
                                    self.pirots_winnings += self.bet * 0.1 * self.purple_lvl
                                case _Pirots_NEW.GREEN_BIRD:
                                    self.pirots_winnings += self.bet * 0.05 * self.green_lvl
                                case _Pirots_NEW.BLUE_BIRD:
                                    self.pirots_winnings += self.bet * 0.05 * self.blue_lvl
                        moved = True

                        if not SIMULATION:
                            await self.msg.edit(embed=self.get_embed(), view=self)
                            await asyncio.sleep(0.2)

        # если были движения — обновляем поле
        if moved:
            self.pirots_move_empty_cells_up()
            if not SIMULATION:
                await self.msg.edit(embed=self.get_embed(), view=self)
                await asyncio.sleep(0.25)

            self.pirots_fill_empty_cells()
            if not SIMULATION:
                await self.msg.edit(embed=self.get_embed(), view=self)
                await asyncio.sleep(0.25)

            # рекурсивно продолжаем, пока птицы могут двигаться
            await self.pirots_move_birds()
        else:
            self.is_spinning = False
            await self.msg.edit(embed=self.get_embed(), view=self) #сообщение о конце

    def pirots_map_gem_cluster(
            self,
            target_gems: list[_Pirots_NEW],
            bird_position: tuple[int, int],
            cluster: list[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        if not cluster:
            cluster.append(bird_position)

        n_rows = len(self.pirots_reels)
        n_cols = len(self.pirots_reels[0])
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

        r0, c0 = bird_position
        for dr, dc in directions:
            nr = r0 + dr
            nc = c0 + dc

            # Теперь проверяем: клетка должна быть одним из допустимых типов
            if 0 <= nr < n_rows and 0 <= nc < n_cols:
                cell = self.pirots_reels[nr][nc]

                # Проверяем, что клетка — допустимый тип (обычный или бонус)
                if cell in target_gems:
                    cluster.append((nr, nc))

                    # Если это обычный самоцвет (5–8), делаем его “CLAIMED” (+4)
                    if 5 <= cell.value <= 8:
                        self.pirots_reels[nr][nc] = _Pirots_NEW(cell.value + 4) #сдвиг на +4 до claimed
                    elif 14 <= cell.value <= 16 or 20 <= cell.value <= 22:
                        # Для бонусных
                        self.pirots_reels[nr][nc] = _Pirots_NEW(cell.value + 3) #сдвиг на +3 до claimed

                    # Продолжаем рекурсию
                    self.pirots_map_gem_cluster(target_gems, (nr, nc), cluster)

        return cluster

    def pirots_move_empty_cells_up(self) -> None:
        """Сдвигает все непустые клетки вниз, чтобы 'заполнить' пустые."""
        n_rows = len(self.pirots_reels)
        n_cols = len(self.pirots_reels[0])

        for c in range(n_cols):
            free_cells: list[int] = []
            for r in range(n_rows - 1, -1, -1):
                if self.pirots_reels[r][c] == _Pirots_NEW.EMPTY:
                    free_cells.append(r)
                elif free_cells:
                    target_r = free_cells.pop(0)
                    self.pirots_reels[target_r][c] = self.pirots_reels[r][c]
                    self.pirots_reels[r][c] = _Pirots_NEW.EMPTY
                    free_cells.append(r)

    def pirots_fill_empty_cells(self) -> None:
        """Заполняет пустые клетки новыми случайными самоцветами."""
        n_rows = len(self.pirots_reels)
        n_cols = len(self.pirots_reels[0])
        for r in range(n_rows):
            for c in range(n_cols):
                if self.pirots_reels[r][c] == _Pirots_NEW.EMPTY:
                    self.pirots_reels[r][c] = _Pirots_NEW.get_random_gem()

    # -------- Контроль игрового цикла --------

    async def set_msg_and_spin(self, msg: discord.Message) -> None:
        """Привязывает сообщение и запускает игровой цикл."""
        #self.is_spinning = True
        self.msg = msg
        await self.spin()

    async def spin(self) -> None:
        """Основной запуск одной игровой сессии."""
        self.player_token_info[0] += int(self.pirots_winnings)

        await self.pirots_reset_board()
        await asyncio.sleep(0.5)
        await self.pirots_move_birds()
        await self.msg.edit(embed=self.get_embed(), view=self)

        # начисляем итог выигрыша
        if self.pirots_winnings > 0:
            self.player_token_info[0] += int(self.pirots_winnings)
            self.pirots_winnings = 0.0

    # -------- Кнопка "Сыграть снова" --------
    @discord.ui.button(label="Сыграть снова")
    async def play_again_btn(self, interaction: discord.Interaction, btn: discord.ui.Button) -> None:
        """Обработчик нажатия кнопки 'Сыграть снова'."""
        if interaction.user.id != self.player_userid:
            await interaction.response.send_message("Не твоя игра сучк", ephemeral=True)
        elif self.is_spinning:
            await interaction.response.send_message("Подожди, пока слоты докрутятся", ephemeral=True)
        elif self.player_token_info[0] >= self.bet:
            btn.disabled = True
            await interaction.response.defer()
            self.stop()

            new_view: View_pirots = View_pirots(self.bet, self.player_userid, self.player_token_info)
            msg: discord.Message = await self.msg.channel.send(str(new_view), view=new_view)
            await new_view.set_msg_and_spin(msg)
        else:
            btn.disabled = True
            await interaction.response.send_message(":prohibited: Недостаточно токенов!", ephemeral=True)
            self.stop()


if __name__ == "__main__":
    print("George Droid Slots Testing Mode Activated")

    class View_Test(View_pirots):

        def __init__(self, bet):
            super().__init__(bet, 1, [10000000])
            self.msg = DummyMessage()               # заглушка Discord сообщения

    async def simulate():

        n = 10000
        bet = 10000
        total = 0
        wins_cnt = 0
        winnings = []

        for _ in range(n):

            view = View_Test(bet)

            await view.pirots_reset_board()
            await view.pirots_move_birds()

            win = view.pirots_winnings

            winnings.append(win)
            total += win

            if win > bet:
                wins_cnt += 1

        winnings.sort()
        print(
            f"\nfor {n} games with bet {bet}:"
            f"\naverage win: {total / n}"
            f"\nmedian win: {winnings[n // 2]}"
            f"\nchance to win: {wins_cnt / n * 100}%"
        )


    asyncio.run(simulate())
