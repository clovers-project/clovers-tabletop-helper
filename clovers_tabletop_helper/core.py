import random
import re
from datetime import datetime
from collections.abc import Sequence


def roll(dice_cmd: str) -> int | None:
    cmds = dice_cmd.split("+")
    result = 0
    for cmd in cmds:
        if cmd.isdigit():
            result += int(cmd)
            continue
        if match := re.match(r"^(\d*)d(\d+)", cmd):
            a, b = match.groups()
            if a:
                a = int(a)
                if a > 100:  # 限制骰子数量
                    return
            else:
                a = 1
            for _ in range(a):
                result += random.randint(1, int(b))
            continue
        return

    return result


class GroupTabletop:
    def __init__(
        self,
        group_id: str,
    ) -> None:
        """
        群桌面
            pile: 牌堆
        """
        self.group_id = group_id
        self.pile: PokerPile | None = None


class PokerPile:
    def __init__(
        self,
        creater: str,
        n: int = 1,
        jokers: bool = True,
        jqk: bool = True,
        x: int = 0,
    ) -> None:
        """
        扑克牌可指定的参数：
        n: 洗n副牌：1
        jokers: 是否包含小丑牌：True
        jqk: 是否包含人头牌：True
        x: 指定单次抽牌张数：0 不限制（默认1张）
        指令示例：
            创建扑克牌 3副牌 无小丑牌 有人头牌 每次抽1张
        """
        self.creater = creater
        self.create_time = datetime.now()
        self.jokers = jokers
        self.jqk = jqk
        self.poker = self.random_poker(n, jokers, jqk)
        self.ptr: int = 0
        self.x = x

    def random_poker(self, n: int, joker: bool, jqk: bool):
        """
        生成随机牌库
        """
        if jqk:
            range_point = 1, 14
        else:
            range_point = 1, 10
        poker_deck = [(suit, point) for suit in range(1, 5) for point in range(*range_point)]

        if joker:
            poker_deck.append((0, 0))
            poker_deck.append((5, 0))

        poker_deck = poker_deck * n
        random.shuffle(poker_deck)
        return poker_deck

    def drawn(self, n: int = 1):
        if self.ptr + n > len(self.poker):
            return None
        hand = self.poker[self.ptr : self.ptr + n]
        self.ptr += n
        return hand

    def info(self) -> str:
        return (
            f"牌堆剩余：{len(self.poker)-self.ptr}\n"
            f"创建日期：{self.create_time.strftime('%m月%d日 %H:%M')}\n"
            f"创建者：{self.creater}\n"
            f"包含小丑牌：{self.jokers}\n"
            f"包含人头牌：{self.jqk}\n"
            f"强制回合抽牌数：{self.x or '无限制'}"
        )

    POKER_SUIT = {4: "♠", 3: "♥", 2: "♣", 1: "♦", 0: "Small", 5: "Big"}
    POKER_POINT = {
        0: "Joker",
        1: " A",
        2: " 2",
        3: " 3",
        4: " 4",
        5: " 5",
        6: " 6",
        7: " 7",
        8: " 8",
        9: " 9",
        10: "10",
        11: " J",
        12: " Q",
        13: " K",
        14: " A",
    }

    @classmethod
    def show_hand(cls, hands: list[tuple[int, int]], split: str = "\n"):
        return split.join(f"【{cls.POKER_SUIT[suit]}{cls.POKER_POINT[point]}】" for suit, point in hands)

    patterns = {
        key: re.compile(pattern)
        for key, pattern in {
            "n": r"(\d+)副牌",
            "jokers": r"(无|有)小丑牌",
            "jqk": r"(无|有)人头牌",
            "x": r"每次抽(\d+)张",
        }.items()
    }

    @classmethod
    def args_parse(cls, args: Sequence[str]):
        kwargs = {}
        patterns = cls.patterns.copy()
        for arg in args:
            for key, pattern in patterns.items():
                match = re.search(pattern, arg)
                if match:
                    kwargs[key] = match.group(1)
                    break
            else:
                continue
            del patterns[key]
        if "n" in kwargs:
            kwargs["n"] = min(int(kwargs["n"]), 100)  # 防止卡片数量过多
        if "x" in kwargs:
            kwargs["x"] = int(kwargs["x"])
        if "jqk" in kwargs:
            kwargs["jqk"] = kwargs["jqk"] == "有"
        if "jokers" in kwargs:
            kwargs["jokers"] = kwargs["jokers"] == "有"
        return kwargs

    @classmethod
    def create(cls, creater: str, args: Sequence[str]):
        return cls(creater, **cls.args_parse(args))


class Manager:
    def __init__(self):
        self._current_tabletop: dict[str, GroupTabletop] = {}

    def __getitem__(self, index: str) -> GroupTabletop:
        if not index in self._current_tabletop:
            self._current_tabletop[index] = GroupTabletop(index)
        return self._current_tabletop[index]
