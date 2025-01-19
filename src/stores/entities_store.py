from telethon import TelegramClient
from telethon.types import *


class EntityStore:
    def __init__(self, client: TelegramClient):
        self._client = client
        self._entities: dict[int, User] = dict()
        
    async def get(self, entity: int) -> TLObject:
        return self._entities.get(entity) or await self._fetch(entity)
              
    async def get_user(self, user_id: int) -> User:
        return await self.get(user_id)
              
    async def get_peer(self, peer: PeerChat | PeerUser | PeerChannel):
        if isinstance(peer, PeerUser):
            return await self.get_user(peer.user_id)
        elif isinstance(peer, PeerChat):
            return await self.get_chat(peer)
    
    async def get_chat(self, chat: PeerChat) -> Chat:
        return await self.get(chat.chat_id)
    
    async def _fetch(self, user_id: int) -> User:
        user = await self._client.get_entity(user_id)
        self._entities[user_id] = user
        return user
    
    def dump(self) -> list[User]:
        dump = list(self._entities.values())
        print(f"Dump {len(dump)} entities")
        return dump
    
    def load(self, entities: list[TLObject]) -> list[TLObject]:
        for entity in entities:
            self._entities[entity.id] = entity
        
        print(f"Load {len(entities)} entities")

__all__ = ['EntityStore']
