from cryptography.fernet import Fernet, InvalidToken

class CipherHandler:
    def __init__(self, key: str | None):
        self._cipher = Fernet(key) if key else None

    def encrypt(self, data: str) -> str:
        if self._cipher:
            return self._cipher.encrypt(data.encode()).decode()
        return data

    def decrypt(self, data: str) -> str:
        if self._cipher:
            return self._cipher.decrypt(data.encode()).decode()
        return data
