from pyrogram.types import Message

from plugins.bot.menu import Menu


class MessageValidator:
    def __init__(
        self,
        menu: Menu,
        message: Message,
        edit_message: Message = None,
        delete_message: Message = None,
    ):
        self.menu = menu
        self.message = message
        self.edit_message = edit_message
        self.delete_message = delete_message

    async def _reply(self, text: str):
        if self.edit_message:
            await self.edit_message.edit_text(
                text=text,
                reply_markup=self.menu.reply_markup,
                disable_web_page_preview=True,
            )
        else:
            await self.message.reply_text(
                text=text,
                reply_markup=self.menu.reply_markup,
                disable_web_page_preview=True,
            )
        if self.delete_message:
            # Удаляем предыдущее меню
            await self.delete_message.delete()

    async def is_text(self) -> bool:
        if not self.message.text:
            await self._reply("❌ Допустимо только текстовое сообщение")
            return False
        return True

    async def is_photo(self) -> bool:
        if not self.message.photo:
            await self._reply("❌ Допустимо только сообщение с изображением")
            return False
        return True

    async def text_length_less_than(self, length: int) -> bool:
        if not self.message.text or len(self.message.text) > length:
            await self._reply(f"❌ Количество символов не должно превышать {length}")
            return False
        return True
