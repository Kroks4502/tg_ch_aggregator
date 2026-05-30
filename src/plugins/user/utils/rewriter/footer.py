from plugins.user.utils.rewriter.item import AbstractItemController
from plugins.user.utils.text_length import tg_len, tg_slice
from settings import TELEGRAM_MAX_CAPTION_LENGTH, TELEGRAM_MAX_TEXT_LENGTH

CROPPED_TEXT = "…\n\n"
LINK_TEXT = "Полное сообщение…"


class FooterController(AbstractItemController):
    """Контроллер создания нижней части сообщения категории."""

    _message = None
    # Telethon: и текст, и подпись медиа хранятся в одном поле message.message
    _text_attr_name = "message"
    _entities_attr_name = "entities"

    def include_to_message(
        self,
        message,
        cropped_text: str = CROPPED_TEXT,
    ) -> None:
        self._message = message
        self._join_items()

        # Определяем максимальную длину: медиа → caption limit, текст → text limit
        is_media = message.media is not None
        max_len = (
            (TELEGRAM_MAX_CAPTION_LENGTH if is_media else TELEGRAM_MAX_TEXT_LENGTH)
            - len(self._additional_item)
            - tg_len(cropped_text)
        )
        if tg_len(self._get_text()) > max_len:
            self._cut_text(max_len, cropped_text=cropped_text)

        self._include_entities_to_message()
        self._include_text_to_message()

    def _cut_text(self, length: int, cropped_text: str = ""):
        # tg_slice заменяет pyrogram Str(text)[:length] — корректный UTF-16 срез
        self._set_text(tg_slice(self._get_text(), length) + cropped_text)
        self._set_entities([e for e in self._get_entities() if e.offset + e.length < length])

    def _include_entities_to_message(self) -> None:
        self._additional_item.shift_entities(tg_len(self._get_text()))
        self._set_entities(self._get_entities() + self._additional_item.entities)

    def _include_text_to_message(self) -> None:
        self._set_text(self._get_text() + self._additional_item.text)
