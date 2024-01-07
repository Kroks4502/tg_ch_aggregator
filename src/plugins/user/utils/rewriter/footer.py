from pyrogram.types import Message
from pyrogram.types.messages_and_media.message import Str

from plugins.user.utils.rewriter.item import AbstractItemController
from plugins.user.utils.text_length import tg_len
from settings import TELEGRAM_MAX_CAPTION_LENGTH, TELEGRAM_MAX_TEXT_LENGTH

CROPPED_TEXT = "…\n\n"
LINK_TEXT = "Полное сообщение…"


class FooterController(AbstractItemController):
    """Контроллер создания нижней части сообщения категории."""

    _message = None
    _text_attr_name = "text"
    _entities_attr_name = "entities"

    def include_to_message(
        self,
        message: Message,
        cropped_text: str = CROPPED_TEXT,
    ) -> None:
        self._message = message
        if not self._message.text:
            self._text_attr_name = "caption"
            self._entities_attr_name = "caption_entities"

        self._join_items()

        max_len = (
            (TELEGRAM_MAX_TEXT_LENGTH if message.text else TELEGRAM_MAX_CAPTION_LENGTH)
            - len(self._additional_item)
            - tg_len(cropped_text)
        )
        if tg_len(message.text or message.caption) > max_len:
            self._cut_text(max_len, cropped_text=cropped_text)

        self._include_entities_to_message()
        self._include_text_to_message()

    def _cut_text(self, length: int, cropped_text: str = ""):
        self._set_text(Str(self._get_text())[:length] + cropped_text)
        self._set_entities(
            [e for e in self._get_entities() if e.offset + e.length < length]
        )

    def _include_entities_to_message(self) -> None:
        self._additional_item.shift_entities(tg_len(self._get_text()))
        self._set_entities(self._get_entities() + self._additional_item.entities)

    def _include_text_to_message(self) -> None:
        self._set_text(self._get_text() + self._additional_item.text)
