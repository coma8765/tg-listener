from abc import ABC

from event_listener import TelegramEventListener
from telethon.types import *


class TelegramHelper(TelegramEventListener, ABC):
    pass

__all__ = ['TelegramHelper']
