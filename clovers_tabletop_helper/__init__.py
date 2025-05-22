from clovers import Event, Plugin, Result, TempHandle
from .manager import Manager, PokerPile, roll

plugin = Plugin()

tabletop_manager = Manager()


@plugin.handle({"桌游小助手帮助"}, {"group_id", "permission"})
async def _(event: Event):
    return Result(
        "text",
        "帮助\n"
        "群牌堆指令示例:\n创建群牌堆 2副牌 无小丑牌 有人头牌 每次抽1张\n"
        "重置群牌堆\n"
        "抽扑克牌\n"
        "本群牌堆信息\n"
        "掷骰帮助\n.r 掷骰\n.rp 劣势掷骰\n.rb 优势掷骰\n示例：.r2d6+d20+1",
    )


def identity(user_id: str, group_id: str):
    def rule(event: Event):
        return event.properties["user_id"] == user_id and event.properties["group_id"] == group_id

    return rule


async def confirm(event: Event, handle: TempHandle):
    handle.finish()
    user_id = event.properties["user_id"]
    group_id = event.properties["group_id"]
    if event.message == "是":
        tabletop = tabletop_manager[group_id]
        assert (state := handle.state) is not None
        tabletop.pile = PokerPile.create(user_id, state)
        return Result("text", f"扑克牌创建成功！\n{tabletop.pile.info()}")
    else:
        return Result("text", "已取消扑克牌创建")


@plugin.handle(["创建群牌堆"], ["user_id", "group_id"])
async def _(event: Event):
    user_id = event.properties["user_id"]
    group_id = event.properties["group_id"]
    tabletop = tabletop_manager[group_id]
    if tabletop.pile:
        plugin.temp_handle(
            ["user_id", "group_id"],
            timeout=60,
            rule=identity(user_id, group_id),
            state=event.args,
        )(confirm)
        return Result("text", f"本群已有扑克牌,是否重新创建？\n【请输入是/否】\n{tabletop.pile.info()}")
    tabletop.pile = PokerPile.create(user_id, event.args)
    return Result("text", f"扑克牌创建成功！\n{tabletop.pile.info()}")


@plugin.handle(["重置群牌堆"], ["group_id"])
async def _(event: Event):
    tabletop_manager[event.properties["group_id"]].pile = None
    return Result("text", "本群扑克牌已重置")


@plugin.handle(["抽扑克牌"], ["group_id"])
async def _(event: Event):
    group_id = event.properties["group_id"]
    pile = tabletop_manager[group_id].pile
    if pile is None:
        return Result("text", "本群没有牌堆，请先输入【创建群牌堆】创建")
    if pile.x:
        n = pile.x
    else:
        if (args := event.args) and args[0].isdigit():
            n = int(args[0])
        else:
            n = 1
    hands = pile.drawn(n)
    if hands is None:
        tabletop_manager[group_id].pile = None
        return Result("text", "牌库没有足够的牌。本群牌堆已重置。")
    else:
        handshow = pile.show_hand(hands)
        rd = len(pile.poker) - pile.ptr
        if rd < 1:
            tabletop_manager[group_id].pile = None
            tips = "牌库已清空"
        else:
            tips = f"剩余牌数{rd}"
        return Result("text", f"{handshow}\n{tips}")


@plugin.handle(["本群牌堆信息"], ["group_id"])
async def _(event: Event):
    pile = tabletop_manager[event.properties["group_id"]].pile
    if pile is None:
        return "本群没有牌堆，请先输入【创建扑克牌】创建"
    return pile.info()


@plugin.handle([".r"], ["user_id"])
async def _(event: Event):
    dice_cmd = event.message[2:]
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

    match mode:
        case "p":
            d2 = roll(dice_cmd)
            assert d2 is not None
            result = f"劣势掷骰{dice_cmd}\n点数为：{min(d1,d2)}({d1},{d2})"
        case "b":
            d2 = roll(dice_cmd)
            assert d2 is not None
            result = f"优势掷骰{dice_cmd}\n点数为：{max(d1,d2)}({d1},{d2})"
        case _:
            result = f"掷骰{dice_cmd}\n点数为：{d1}"

    return Result("list", [Result("at", event.properties["user_id"]), Result("text", result)])


__plugin__ = plugin
