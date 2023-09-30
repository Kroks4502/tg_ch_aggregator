from pyrogram import types

from plugins.bot.buttons import ButtonAdder
from plugins.bot.validators import is_admin
from utils.menu import MenuAbstract


class Menu(MenuAbstract):
    button_adder = ButtonAdder
    add_button: ButtonAdder

    def __init__(
        self,
        path: str,
        *,
        user: types.User,
        back_title: str = "Назад",
        back_step: int = 1,
    ):
        """
        :param path: Текущий путь меню.
        :param back_title: Текст кнопки "Назад".
        :param back_step: Количество шагов для кнопки "Назад".
        """
        super().__init__(path=path, back_title=back_title, back_step=back_step)
        self.user = user

    def is_admin_user(self):
        return is_admin(self.user.id)
