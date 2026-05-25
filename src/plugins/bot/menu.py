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
        user_id: int,
        back_title: str = "Назад",
        back_step: int = 1,
    ):
        """
        :param path: Текущий путь меню.
        :param user_id: Telegram-id пользователя, для которого строится меню.
        :param back_title: Текст кнопки "Назад".
        :param back_step: Количество шагов для кнопки "Назад".
        """
        super().__init__(path=path, back_title=back_title, back_step=back_step)
        self.user_id = user_id

    @property
    def user(self):
        """Совместимость: handler'ы читают menu.user.id. Lazy-объект с одним полем."""
        return _UserRef(self.user_id)

    def is_admin_user(self):
        return is_admin(self.user_id)


class _UserRef:
    __slots__ = ("id",)

    def __init__(self, user_id: int):
        self.id = user_id
