import pickle
from telethon import events
import asyncio
import signal

from config import AppConfig
from src.handlers import EventHandlers
from src.services.crypt import CipherHandler
from src.log_store import LogStoreManager
from src.services.tg import TelegramEventListener


class EventLogger(TelegramEventListener):
    def __init__(self, config: AppConfig):
        # Настройка компонентов
        self._config = config
        self.cipher_handler = CipherHandler(config.journal_key)
        super().__init__(self._config.tg_api_id, self._config.tg_api_hash)
        
        self.store_manager = LogStoreManager(self._client)
        
        # Создание обработчиков событий
        self.handlers = EventHandlers(
            self._client,
            self._config,
            self.store_manager,
            self.cipher_handler,
        )
        
        # Добавляем обработчики событий в клиент
        self._client.add_event_handler(self.handlers.all_events_handler, event=events.Raw)
        self._client.add_event_handler(self.handlers.typing_message_action, event=events.UserUpdate)
        self._client.add_event_handler(self.handlers.delete_message_action, event=events.MessageDeleted)
        self._client.add_event_handler(self.handlers.edit_message_action, event=events.MessageEdited)
        self._client.add_event_handler(self.handlers.new_message_action, event=events.NewMessage)

    async def all_events_handler(self, event):     
        pass

    async def start(self, loop: asyncio.AbstractEventLoop):
        """
        Метод для запуска клиента Telegram и загрузки данных из хранилища.
        """
        self._loop = loop
        loop.add_signal_handler(signal.SIGINT, lambda: asyncio.ensure_future(self.stop()))

        # Загружаем данные из локального хранилища
        try:
            if self.cipher_handler.cipher is None:
                with open("data.raw", "rb") as f:
                    data = pickle.load(f)
            else:
                with open("data.raw.enc", "rb") as f:
                    decrypted_data = self.cipher_handler.cipher.decrypt(f.read())
                    data = pickle.loads(decrypted_data)
        except FileNotFoundError:
            print("Store not found!")
            data = None

        # Если данные существовали, загружаем их в хранилище
        if data is not None:
            self.store_manager.load(data["entities"], data["messages"])

        # Запускаем Telegram клиент
        await super().start()

    async def stop(self):
        """
        Метод для остановки клиента Telegram и сохранения данных в локальное хранилище.
        """
        print("Штатное завершение работы EventLogger...")
        print("Отключение клиента Telegram...")
        try:
            await self._client.disconnect()

            print("Сохранение данных в локальное хранилище...")
            dump_data = self.store_manager.dump()

            if self.cipher_handler.cipher is None:
                with open("data.raw", "wb") as f:
                    pickle.dump(dump_data, f)
            else:
                with open("data.raw.enc", "wb") as f:
                    f.write(self.cipher_handler.cipher.encrypt(pickle.dumps(dump_data)))
        finally:
            self._loop.stop()


async def main():
    # Конфигурация приложения
    config = AppConfig()
    event_logger = EventLogger(config)

    loop = asyncio.get_event_loop()
    await event_logger.start(loop)
    await loop.run_forever()

# Запуск приложения
if __name__ == "__main__":
    asyncio.run(main())
