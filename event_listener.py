from abc import abstractmethod, ABC

from telethon import TelegramClient, events


class TelegramEventListener(ABC):
    def __init__(self, api_id, api_hash, session_name='event_listener'):
        """
        Инициализация клиента Telegram для прослушивания событий.

        :param api_id: API ID, полученный из https://my.telegram.org/apps
        :param api_hash: API HASH, полученный из https://my.telegram.org/apps
        :param session_name: Имя сессии Telegram (по умолчанию 'event_listener').
        """
        self._client = TelegramClient(session_name, api_id, api_hash)

    async def setup_handlers(self):
        """
        Установка обработчиков событий.
        """
        self._client.add_event_handler(self.all_events_handler, event=events.Raw)
        # self._client.add_event_handler(self.all_events_handler, event=events.NewMessage)
        # self._client.add_event_handler(self.all_events_handler, event=events.MessageEdited)
        # self._client.add_event_handler(self.all_events_handler, event=events.MessageDeleted)
        # self._client.add_event_handler(self.all_events_handler, event=events.Album)
        # self._client.add_event_handler(self.all_events_handler, event=events.ChatAction)
        # self._client.add_event_handler(self.all_events_handler, event=events.UserUpdate)

    @abstractmethod
    async def all_events_handler(event):
        pass

    async def start(self):
        """
        Запуск клиента Telegram и его выполнение до отключения.
        """
        print("Запуск клиента Telegram...")
        await self._client.start()
        await self.setup_handlers()

        print("Клиент успешно запущен. Ожидание событий...")
        await self._client.run_until_disconnected()

class _Sample(TelegramEventListener):
    async def all_events_handler(event):
        print("New event: ${event}")


# Пример использования класса
if __name__ == "__main__":
    import asyncio

    from config import AppConfig

    config = AppConfig()

    # Создание экземпляра класса
    listener = _Sample(config.tg_api_id, config.tg_api_hash)

    # Запуск клиента через asyncio
    asyncio.run(listener.start())
