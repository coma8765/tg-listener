import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


class EncryptedEnvironment:
    def __init__(self, encryption_key: str):
        """
        Инициализация класса с ключом шифрования.
        
        :param encryption_key: Строка с ключом шифрования, используемым для шифрования и дешифрования.
        """
        
        self.cipher = Fernet(encryption_key)
        load_dotenv(".env")

    def encrypt_value(self, value: str) -> str:
        """
        :param key: Имя переменной в окружении (например, "MY_VAR").
        :param value: Значение переменной для сохранения.
        """
        return self.cipher.encrypt(value.encode()).decode()

    def decrypt_value(self, value: str) -> str:
        """
        :param key: Имя переменной в окружении (например, "MY_VAR").
        :param value: Значение переменной для сохранения.
        """
        return self.cipher.decrypt(value.encode()).decode()

    def get_encrypted_env(self, key: str) -> str:
        """
        Получает значение переменной окружения, расшифровывая его.

        :param key: Имя переменной в окружении (например, "MY_VAR").
        :return: Расшифрованное значение переменной.
        :raises KeyError: Если переменной с данным ключом нет в окружении.
        """
        if key not in os.environ:
            print(os.environ)
            raise KeyError(f"Переменной окружения с именем '{key}' не найдено.")

        encrypted_value = os.environ[key]
        return self.cipher.decrypt(encrypted_value.encode()).decode()


class AppConfig:
    def __init__(self, sec_key: str | None = None):
        if (sec_key is None):
            sec_key = os.getenv("SEC_KEY") or None

        if (sec_key is None):
            sec_key = input("Введите ключ шифрования: ")

        self._env_manager = EncryptedEnvironment(sec_key)
        
    @property
    def tg_api_id(self) -> str:
        return self._env_manager.get_encrypted_env("ENCRYPTED_TG_API_ID")

    @property
    def tg_api_hash(self) -> str:
        return self._env_manager.get_encrypted_env("ENCRYPTED_TG_API_HASH")
    
    @property
    def journal_key(self) -> str:
        return self._env_manager.get_encrypted_env("ENCRYPTED_JOURNAL_KEY")
    
    @property
    def fwd_chat_id(self) -> str:
        return int(self._env_manager.get_encrypted_env("ENCRYPTED_FWD_MSG_CHAT_ID"))
    
    @property
    def journal_chat_id(self) -> str:
        return int(self._env_manager.get_encrypted_env("ENCRYPTED_JOURNAL_CHAT_ID"))

    def __str__(self):
        return (
            f"AppConfig("
            f"tg_api_id={self.tg_api_id}, "
            f"tg_api_hash={'*' * len(self.tg_api_hash) if self.tg_api_hash else None}, "
            f"journal_key={'*' * len(self.journal_key) if self.journal_key else None}, "
            f"fwd_chat_id={self.fwd_chat_id}, "
            f"journal_chat_id={self.journal_chat_id})"
        )
