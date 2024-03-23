from telethon import events
from telethon.tl import custom

MessageEventType = events.NewMessage.Event | custom.Message
