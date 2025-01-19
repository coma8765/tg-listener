
from src.stores.entities_store import EntityStore
from src.stores.message_store import MessageStore


class LogStoreManager:
    def __init__(self, client):
        self.entity_store = EntityStore(client)
        self.message_store = MessageStore()

    def load(self, entities, messages):
        self.entity_store.load(entities)
        self.message_store.load(messages)

    def dump(self):
        return {
            "entities": self.entity_store.dump(),
            "messages": self.message_store.dump(),
        }

