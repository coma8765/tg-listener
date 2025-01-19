import asyncio

import datetime
import pickle
import signal
from event_listener import TelegramEventListener
from cryptography.fernet import Fernet, InvalidToken
from telethon import TelegramClient, events, types, errors

from config import AppConfig


class EntityStore:
    def __init__(self, client: TelegramClient):
        self._client = client
        self._entities: dict[int, types.User] = dict()
        
    async def get(self, entity: int) -> types.TLObject:
        return self._entities.get(entity) or await self._fetch(entity)
              
    async def get_user(self, user_id: int) -> types.User:
        return await self.get(user_id)
              
    async def get_peer(self, peer: types.PeerChat | types.PeerUser | types.PeerChannel):
        if isinstance(peer, types.PeerUser):
            return await self.get_user(peer.user_id)
        elif isinstance(peer, types.PeerChat):
            return await self.get_chat(peer.chat_id)
    
    async def get_chat(self, chat_id: int) -> types.Chat:
        return await self.get(chat_id)
    
    async def _fetch(self, user_id: int) -> types.User:
        user = await self._client.get_entity(user_id)
        self._entities[user_id] = user
        return user
    
    def dump(self) -> list[types.User]:
        dump = list(self._entities.values())
        print(f"Dump {len(dump)} entities")
        return dump
    
    def load(self, entities: list[types.TLObject]) -> list[types.TLObject]:
        for entity in entities:
            self._entities[entity.id] = entity
        
        print(f"Load {len(entities)} entities")


class MessageStore:
    def __init__(self):
        self._messages: dict[int, tuple[types.Message, str | None]] = dict()
        
    def get(self, msg_id: int) -> types.Message | None:
        return self._messages.get(msg_id, (None, None))[0]

    def get_fwd_link(self, msg_id: int) -> str | None:
        return self._messages.get(msg_id, (None, None))[1]
    
    def set(self, msg: types.Message):
        self._messages[msg.id] = (msg, None)
    
    def set_fwd_link(self, msg: types.Message, link: str):
        self._messages[msg.id] = (msg, link)
    
    def dump(self) -> list[types.Message]:
        dump = [(i[0].to_json(), i[1]) for i in list(self._messages.values())]
        print(f"Dump {len(dump)} messages")
        
        return dump
    
    def load(self, entities: list[tuple[types.Message, str | None]]):
        for msg in self._messages.values():
            self._messages[msg[0].id] = msg

        print(f"Load {len(entities)} messages")


class EventLogger(TelegramEventListener):
    def __init__(self, config: AppConfig):
        super().__init__(config.tg_api_id, config.tg_api_hash)
        
        self._entity_store = EntityStore(self._client)
        self._message_store = MessageStore()

        self._cipher = config.journal_key is not None and Fernet(config.journal_key) or None
        
        if self._cipher is  None:
            print("Warning: encryption doesn't used!")
        
        
        self.__config: AppConfig = config
        
        # Handlers
        self._client.add_event_handler(self.typing_message_action, event=events.UserUpdate)
        self._client.add_event_handler(self.delete_message_action, event=events.MessageDeleted)
        self._client.add_event_handler(self.edit_message_action, event=events.MessageEdited)
        self._client.add_event_handler(self.new_message_action, event=events.NewMessage)
        
    async def typing_message_action(self, event: events.UserUpdate.Event):
        user = await self._entity_store.get_user(event.user_id)
        
        last_msg: types.Message = (await self._client.get_messages(self.__config.journal_chat_id, limit=1))[0]
        
        chat = await self._entity_store.get_chat(event.chat_id)
        if isinstance(chat, types.User):
            chat_text = 'private'
        else:
            chat_text = f"in \"{chat.title}\" ({chat.id})"
        
        msg_text_prefix = f"TYPING from: {user.first_name} {user.last_name} (@{user.username}|{user.id}) {chat_text}"
        msg_text = f"{msg_text_prefix} {datetime.datetime.now().strftime('%H:%M:%S')}"
        
        if last_msg.message.startswith(msg_text_prefix):
            await self._client.edit_message(self.__config.journal_chat_id, last_msg.id, msg_text)
        else:        
            await self._client.send_message(self.__config.journal_chat_id, msg_text)
    
    async def all_events_handler(self, event):     
        if self._cipher is None:
            with open("events.jsonl", "a") as f:
                f.write(event.to_json())
                f.write("\n")     
        else:
            with open("events.jsonl.enc", "a") as f:
                f.write(self._cipher.encrypt(str(event.to_json()).encode()).decode())
                f.write("\n")
            
    async def new_message_action(self, event: events.newmessage.NewMessage.Event):
        self._message_store.set(event.message)

        if isinstance(event.message.peer_id, types.PeerUser):        
            await self._entity_store.get_user(event.message.peer_id.user_id)

        message: types.TypeMessage = event.message

        try:
            msg = await self._client.forward_messages(self.__config.fwd_chat_id, message.id, from_peer=message.peer_id)
        except errors.rpcerrorlist.ChatForwardsRestrictedError as e:
            msg = (await self._client.get_messages(self.__config.fwd_chat_id, limit=1))[0]

        self._message_store.set_fwd_link(message, f"https://t.me/c/{self.__config.fwd_chat_id}/{msg.id}")

    async def edit_message_action(self, event: types.UpdateEditMessage):
        message = event.message
        user =  await self._entity_store.get_peer(message.from_id or message.peer_id)

        preview_msg = self._message_store.get(message.id)
        old_link = self._message_store.get_fwd_link(message.id)
        
        self._message_store.set(message)
        try:
            msg = await self._client.forward_messages(self.__config.fwd_chat_id, message.id, from_peer=message.peer_id)
            new_link = f"https://t.me/c/{self.__config.fwd_chat_id}/{msg.id}"
        except errors.rpcerrorlist.ChatForwardsRestrictedError as e:
            new_link = None

        self._message_store.set_fwd_link(message, new_link)

        msg_text = f"EDIT from: {user.first_name} {user.last_name} (@{user.username}|{user.id})\n\n" \
            f"[before]({old_link or ''}): {preview_msg and preview_msg.message or ''}\n\n" \
            f"[after]({new_link or ''}): {event and message.message or ''}"

        await self._client.send_message(self.__config.journal_chat_id, msg_text)
        
    async def delete_message_action(self, event: events.MessageDeleted.Event):
        chat: types.Chat = event.chat
        
        preview_msgs_with_links = [
            (self._message_store.get(msg_id), self._message_store.get_fwd_link(msg_id))
            for msg_id in event.deleted_ids or []
        ]

        text = "\n".join(
            [
                f"[before]({link}): {msg and msg.message or ''}"
                for msg, link in preview_msgs_with_links
            ]
        )
        
        if preview_msgs_with_links[0][0] is not None:
            if isinstance(preview_msgs_with_links[0][0].peer_id, types.PeerUser):
                user = await self._entity_store.get_user(preview_msgs_with_links[0][0].peer_id.user_id)
                user_text = f"{user.first_name} {user.last_name} (@{user.username}|{user.id})"
            else:            
                user = await self._entity_store.get_chat(preview_msgs_with_links[0][0].peer_id.chat_id)
                user_text = f"\"{user.title}\" ({user.id})"
        else:
            user_text = None

        msg = f"REMOVE msg from {user_text or ''}:\n{text}"

        await self._client.send_message(self.__config.journal_chat_id, msg)

    async def start(self, loop: asyncio.EventLoop):
        self._loop = loop
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.ensure_future(self.stop()))

        try:
            if self._cipher is None:
                with open("data.raw", "r") as f:
                    data = pickle.load(f)
            else:
                with open("data.raw.enc", "rb") as f:
                    data = pickle.loads(self._cipher.decrypt(f.read()))
        except FileNotFoundError:
            print("Store not found")
            data = None
        except InvalidToken:
            print("Invalid data")
            data = None

        if data is not None:
            self._entity_store.load(data["entities"])
            self._message_store.load(data["messages"])
        
        await super().start()

    async def stop(self):
        print("Shutdown...")
        print("Disconnecting...")
        try:
            await self._client.disconnect()
            
            print("Store data...")
            entities_dumps = self._entity_store.dump()
            messages_dumps = self._message_store.dump()
            
            data = {
                "entities": entities_dumps,
                "messages": messages_dumps,
            }
            
            if self._cipher is None:
                with open("data.raw", "a") as f:
                    f.write(pickle.dumps(data))
            else:
                with open("data.raw.enc", "ab") as f:
                    f.write(self._cipher.encrypt(pickle.dumps(data)))        
        finally:
            self._loop.stop()
                
if __name__ == "__main__":
    from config import AppConfig

    # Создание экземпляра класса
    listener = EventLogger(AppConfig())
    
    loop = asyncio.get_event_loop()

    # Запуск клиента через asyncio
    loop.create_task(listener.start(loop))
    loop.run_forever()
