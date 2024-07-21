import re
from collections.abc import Sequence

from clovers.core.plugin import Plugin, Result
from .clovers import Event
from .manager import Manager, PokerPile, roll


def build_result(result):
    if isinstance(result, str):
        return Result("text", result)
    if isinstance(result, list):
        return Result("list", [build_result(seg) for seg in result])
    return result


plugin = Plugin(
    build_event=lambda event: Event(event),
    build_result=build_result,
)

tabletop_manager = Manager()


@plugin.handle({"桌游小助手帮助"}, {"group_id", "permission"})
async def _(event: Event):
    return (
        "帮助\n"
        "群牌堆指令示例:\n创建群牌堆 2副牌 无小丑牌 有人头牌 每次抽1张\n"
        "重置群牌堆\n"
        "抽扑克牌\n"
        "本群牌堆信息\n"
        "掷骰帮助\n.r 掷骰\n.rp 劣势掷骰\n.rb 优势掷骰\n示例：.r2d6+d20+1"
    )


@plugin.handle(["创建群牌堆"], {"user_id", "group_id"})
async def _(event: Event):
    def args_parse(args: Sequence[str]):
        patterns = {
            "n": r"(\d+)副牌",
            "jokers": r"(无|有)小丑牌",
            "jqk": r"(无|有)人头牌",
            "x": r"每次抽(\d+)张",
        }
        kwargs = {}
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

    user_id = event.user_id
    group_id = event.group_id
    tabletop = tabletop_manager[group_id]
    if tabletop.pile:

        @plugin.temp_handle(f"{user_id} {group_id}", extra_args={"user_id", "group_id"}, timeout=60)
        async def _(t_event: Event, finish: Plugin.Finish):
            if t_event.user_id != user_id or t_event.group_id != group_id:
                return
            finish()
            if t_event.event.raw_command == "是":
                tabletop.pile = PokerPile(user_id, **args_parse(event.event.args))
                return f"扑克牌创建成功！\n{tabletop.pile.info()}"
            else:
                return "已取消扑克牌创建"

        return f"本群已有扑克牌,是否重新创建？\n【请输入是/否】\n{tabletop.pile.info()}"
    tabletop.pile = PokerPile(user_id, **args_parse(event.event.args))
    return f"扑克牌创建成功！\n{tabletop.pile.info()}"


@plugin.handle({"重置群牌堆"}, {"group_id", "permission"})
async def _(event: Event):
    tabletop_manager[event.group_id].pile = None
    return "本群扑克牌已重置"


@plugin.handle({"抽扑克牌"}, {"group_id"})
async def _(event: Event):
    pile = tabletop_manager[event.group_id].pile
    if pile is None:
        return "本群没有牌堆，请先输入【创建扑克牌】创建"
    if pile.x:
        n = pile.x
    else:
        if (args := event.event.args) and args[0].isdigit():
            n = int(args[0])
        else:
            n = 1
    hands = pile.drawn(n)
    if hands is None:
        tabletop_manager[event.group_id].pile = None
        return "牌库没有足够的牌。本群牌堆已重置。"
    else:
        handshow = pile.show_hand(hands)
        rd = len(pile.poker) - pile.ptr
        if rd < 1:
            tabletop_manager[event.group_id].pile = None
            tips = "牌库已清空"
        else:
            tips = f"剩余牌数{rd}"
        return f"{handshow}\n{tips}"


@plugin.handle({"本群牌堆信息"}, {"group_id"})
async def _(event: Event):
    pile = tabletop_manager[event.group_id].pile
    if pile is None:
        return "本群没有牌堆，请先输入【创建扑克牌】创建"
    return pile.info()


@plugin.handle({".r"}, {"user_id"})
async def _(event: Event):
    dice_cmd = event.event.raw_command[2:]
    if dice_cmd.startswith("p"):
        dice_cmd = dice_cmd[1:]
        mode = "p"
    elif dice_cmd.startswith("b"):
        dice_cmd = dice_cmd[1:]
        mode = "b"
    else:
        mode = "n"
    d1 = roll(dice_cmd)
    if not d1:
        return
    if mode == "p":
        d2 = roll(dice_cmd)
        assert d2
        return [Result("at", event.user_id), f"劣势掷骰{dice_cmd}\n点数为：{min(d1,d2)}({d1},{d2})"]
    if mode == "b":
        d2 = roll(dice_cmd)
        assert d2
        return [Result("at", event.user_id), f"优势掷骰{dice_cmd}\n点数为：{max(d1,d2)}({d1},{d2})"]
    else:
        return [Result("at", event.user_id), f"掷骰{dice_cmd}\n点数为：{d1}"]


__plugin__ = plugin
