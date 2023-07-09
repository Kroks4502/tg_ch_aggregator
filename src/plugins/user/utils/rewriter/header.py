from pyrogram.types import Message

from plugins.user.utils.rewriter.item import AbstractItemController

SRC_TEXT_TMPL = '💬 Источник: {}'
FWD_TEXT_TMPL = 'fwd: {}'


class HeaderController(AbstractItemController):
    """Контроллер создания верхней части сообщения категории."""

    _message = None
    _text_attr_name = "text"
    _entities_attr_name = "entities"

    def include_to_message(self, message: Message, end_text: str = "") -> None:
        self._message = message
        if not self._message.text:
            self._text_attr_name = "caption"
            self._entities_attr_name = "caption_entities"

        self._join_items(end_text=end_text)

        self._shift_offset_entities()
        self._include_text_to_message()
        self._include_entities_to_message()

    def _shift_offset_entities(self) -> None:
        for entity in self._get_entities():
            entity.offset += len(self._additional_item)

    def _include_text_to_message(self) -> None:
        self._set_text(self._additional_item.text + self._get_text())

    def _include_entities_to_message(self) -> None:
        self._set_entities(self._additional_item.entities + self._get_entities())
