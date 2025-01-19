import datetime
from telethon import events, types, errors
from cryptography.fernet import Fernet

class EventHandlers:
    def __init__(self, client, config, store_manager, cipher_handler):
        self._client = client
        self.config = config
        self.store_manager = store_manager
        self.cipher_handler = cipher_handler
        
        self._cipher = config.journal_key is not None and Fernet(config.journal_key) or None
        
        if self._cipher is  None:
            print("Warning: encryption doesn't used!")

    @property
    def _entity_store(self):
        return self.store_manager.entity_store

    @property
    def _message_store(self):
        return self.store_manager.message_store

    async def last_journal_message(self) -> types.Message | None:
        return (await self._client.get_messages(types.PeerChat(self.config.journal_chat_id), limit=1))[0]

    async def typing_message_action(self, event: events.UserUpdate.Event):
        if not isinstance(event.action, types.SendMessageTypingAction):
            return

        user: types.User = await self._entity_store.get_user(event.user_id)
        last_msg: types.Message = await self.last_journal_message()
        
        chat = await self._entity_store.get_chat(types.PeerChat(event.chat_id))
        if isinstance(chat, types.User):
            chat_text = 'private'
        else:
            chat_text = f"in \"{chat.title}\" ({chat.id})"
        
        msg_text_prefix = f"TYPING from: {user.first_name} {user.last_name} (@{user.username}|{user.id}) {chat_text}"
        msg_text = f"{msg_text_prefix} {datetime.datetime.now().strftime('%H:%M:%S')}"
        
        if last_msg and last_msg.message.startswith(msg_text_prefix):
            await self._client.edit_message(types.PeerChat(self.config.journal_chat_id), last_msg.id, msg_text)
        elif msg_text != last_msg.message:        
            await self._client.send_message(types.PeerChat(self.config.journal_chat_id), msg_text)

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
            msg = await self._client.forward_messages(types.PeerChannel(self.config.fwd_chat_id), message.id, from_peer=message.peer_id)
        except errors.rpcerrorlist.ChatForwardsRestrictedError as e:
            msg = (await self._client.get_messages(types.PeerChannel(self.config.fwd_chat_id), limit=1))[0]

        self._message_store.set_fwd_link(message, f"https://t.me/c/{self.config.fwd_chat_id}/{msg.id}")

    async def edit_message_action(self, event: types.UpdateEditMessage):
        message = event.message
        user =  await self._entity_store.get_peer(message.from_id or message.peer_id)

        preview_msg = self._message_store.get(message.id)
        old_link = self._message_store.get_fwd_link(message.id)
        
        self._message_store.set(message)
        try:
            msg = await self._client.forward_messages(types.PeerChannel(self.config.fwd_chat_id), message.id, from_peer=message.peer_id)
            new_link = f"https://t.me/c/{self.config.fwd_chat_id}/{msg.id}"
        except errors.rpcerrorlist.ChatForwardsRestrictedError as e:
            new_link = None

        self._message_store.set_fwd_link(message, new_link)

        msg_text = f"EDIT from: {user.first_name} {user.last_name} (@{user.username}|{user.id})\n\n" \
            f"[before]({old_link or ''}): {preview_msg and preview_msg.message or ''}\n\n" \
            f"[after]({new_link or ''}): {event and message.message or ''}"

        await self._client.send_message(types.PeerChat(self.config.journal_chat_id), msg_text)
        
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
                user = await self._entity_store.get_chat(types.PeerChat(preview_msgs_with_links[0][0].peer_id.chat_id))
                user_text = f"\"{user.title}\" ({user.id})"
        else:
            user_text = None

        msg = f"REMOVE msg from {user_text or ''}:\n{text}"

        await self._client.send_message(types.PeerChat(self.config.journal_chat_id), msg)
