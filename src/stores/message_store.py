from telethon.tl.types import Message

class MessageStore:
    def __init__(self):
        self._messages: dict[int, tuple[Message, str | None]] = dict()
        
    def get(self, msg_id: int) -> Message | None:
        return self._messages.get(msg_id, (None, None))[0]

    def get_fwd_link(self, msg_id: int) -> str | None:
        return self._messages.get(msg_id, (None, None))[1]
    
    def set(self, msg: Message):
        self._messages[msg.id] = (msg, None)
    
    def set_fwd_link(self, msg: Message, link: str):
        self._messages[msg.id] = (msg, link)
    
    def dump(self) -> list[Message]:
        dump = [(i[0].to_json(), i[1]) for i in list(self._messages.values())]
        print(f"Dump {len(dump)} messages")
        
        return dump
    
    def load(self, entities: list[tuple[Message, str | None]]):
        for msg in self._messages.values():
            self._messages[msg[0].id] = msg

        print(f"Load {len(entities)} messages")

__all__ = ['MessageStore']
