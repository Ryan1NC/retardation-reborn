import discord

import asyncio
import cProfile
import unittest
from unittest.mock import (
    MagicMock,
    AsyncMock
)

import sys

sys.path.append(sys.path[0] + "\\\\..")

from src import slots_new as slots


class TestSlotsView(unittest.TestCase):
    def test_slots_average_winnings(self):
        bet: int = 100
        userid: int = 42
        token_info: list[int] = [10000, 0, 0]

        spins_cnt: int = 5000
        spins_results: list[int] = []
        spins_results_sum: int = 0

        pirots_cnt: int = 0
        pirots_results: list[int] = []
        pirots_results_sum: int = 0

        discord.ui.View.__init__ = MagicMock()

        msg: discord.Message = AsyncMock()
        discord.Message.edit = AsyncMock()

        asyncio.sleep = AsyncMock()

        slots.View_pirots.__str__ = MagicMock(return_value="")

        for _ in range(spins_cnt):
            token_info[0] = bet
            slotsView: slots.View_pirots = slots.View_pirots(bet, userid, token_info)

            asyncio.run(slotsView.set_msg_and_spin(msg))

            spins_results.append(token_info[0])
            spins_results_sum += token_info[0]

            pirots_winnings = int(slotsView.pirots_winnings)
            if pirots_winnings > 0:
                pirots_cnt += 1
                pirots_results.append(pirots_winnings)
                pirots_results_sum += pirots_winnings

        average: float = spins_results_sum / spins_cnt
        spins_results = sorted(spins_results)
        median: int = spins_results[spins_cnt // 2]

        print(f"For {spins_cnt} spins with the bet of {bet}:")
        print(f"    - Average winnings: {average:.2f}")
        print(f"    - Median winnings: {median}")

        if pirots_cnt > 0:
            pirots_chance: float = pirots_cnt / spins_cnt * 100.0
            pirots_average: float = pirots_results_sum / pirots_cnt
            pirots_results = sorted(pirots_results)
            pirots_median: int = pirots_results[pirots_cnt // 2]
            pirots_min: int = pirots_results[0]
            pirots_max: int = pirots_results[len(pirots_results) - 1]

            print(f"    - Pirots info:")
            print(f"        - Chances of a pirots bonus game: {pirots_chance:.2f}%")
            print(f"        - Average winnings across {pirots_cnt} bonus games: {pirots_average:.2f}")
            print(f"        - Median winnings: {pirots_median}")
            print(f"        - Min winnigs: {pirots_min}")
            print(f"        - Max winnigs: {pirots_max}")

        print()

        #self.assertLess(average, bet)
        self.assertLess(median, bet)

    def test_pirots_get_random_board(self):
        board = slots._Pirots_NEW.get_random_board()
        birds_in_board = []
        ALL_BIRDS = [slots._Pirots_NEW.RED_BIRD, slots._Pirots_NEW.PURPLE_BIRD, slots._Pirots_NEW.GREEN_BIRD,
                     slots._Pirots_NEW.BLUE_BIRD]

        for x in range(len(board)):
            for y in range(len(board[0])):
                self.assertIsInstance(board[x][y], slots._Pirots_NEW)

                if board[x][y] in ALL_BIRDS:
                    birds_in_board.append(board[x][y])

        birds_in_board = sorted(birds_in_board, key=lambda x: x.value)
        self.assertListEqual(birds_in_board, ALL_BIRDS)


if __name__ == "__main__":
    # cProfile.run("unittest.main()")
    unittest.main()
