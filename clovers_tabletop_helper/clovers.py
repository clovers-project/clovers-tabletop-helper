from clovers import Event as CloversEvent


class Event:
    def __init__(self, event: CloversEvent):
        self.event: CloversEvent = event

    @property
    def command(self) -> str:
        return self.event.raw_command

    @property
    def user_id(self) -> str:
        return self.event.properties["user_id"]

    @property
    def group_id(self) -> str:
        return self.event.properties["group_id"]
