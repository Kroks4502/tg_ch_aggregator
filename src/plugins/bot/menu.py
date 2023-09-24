from pyrogram import types

from models import AlertRule, Category, Filter, Source, User
from plugins.bot.buttons import ButtonAdder
from plugins.bot.text import get_breadcrumbs
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

    async def get_text(
        self,
        *,
        start_text: str = None,
        last_text: str = None,
        category_obj: Category = None,
        source_obj: Source = None,
        filter_obj: Filter = None,
        filter_type_id: str = None,
        cleanup_pattern: str = None,
        user_obj: User = None,
        alert_rule_obj: AlertRule = None,
    ) -> str:
        breadcrumbs = await get_breadcrumbs(
            category_obj=category_obj,
            source_obj=source_obj,
            filter_obj=filter_obj,
            filter_type_id=filter_type_id,
            cleanup_pattern=cleanup_pattern,
            user_obj=user_obj,
            alert_rule_obj=alert_rule_obj,
        )
        menu_text = super().get_text(start_text=start_text, last_text=last_text)
        result = "\n\n".join((breadcrumbs, menu_text))
        return result or "<пусто>"

    def is_admin_user(self):
        return is_admin(self.user.id)
