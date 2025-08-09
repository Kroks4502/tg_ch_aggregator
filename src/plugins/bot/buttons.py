from typing import Iterable, Type

from peewee import Expression

from models import AlertRule, BaseModel, Category, Filter, Source
from utils.menu import ButtonAdderBase, ButtonData

CATEGORIES_BTN = ButtonData(title="🗂 Категории", path="c")
SOURCES_BTN = ButtonData(title="📚 Источники", path="s")
FILTERS_BTN = ButtonData(title="🪤 Фильтры", path="ft")
CLEANUPS_BTN = ButtonData(title="🧹 Очистка", path="cl")
ALERT_RULES_BTN = ButtonData(title="🔔 Уведомления", path="r")
READ_BTN = ButtonData(title="📖 Читать", path="rd")
MESSAGES_HISTORIES_BTN = ButtonData(title="📖 Сообщения", path="mh")
STATISTICS_BTN = ButtonData(title="📊 Статистика", path="stat")
CHECK_POST_BTN = ButtonData(title="🚧 Проверить пост", path=":check_post")
OPTIONS_BTN = ButtonData(title="🛠 Настройки", path="o")

FILTERS_HISTORIES_BTN = ButtonData(title="📙 История фильтрации", path="fh")

ADD_BTN = ButtonData(title="➕ Добавить", path=":add")
ADD_MINI_BTN = ButtonData(title="➕", path=":add")

EDIT_BTN = ButtonData(title="📝 Изменить", path=":edit")
EDIT_MINI_BTN = ButtonData(title="📝", path=":edit")

DELETE_BTN = ButtonData(title="✖️ Удалить", path=":delete")
DELETE_MINI_BTN = ButtonData(title="✖️", path=":delete")

CONFIRMATION_DELETE_BTN = ButtonData(title="❌ Подтвердить удаление", path=":y")


class ButtonAdder(ButtonAdderBase):
    def _add_row_button(
        self,
        button: ButtonData,
        model: Type["BaseModel"] = None,
        where: Expression = None,
        amount: str | int = None,
        back_step: int = 0,
    ):
        if model:
            select = model.select()
            amount = (select if not where else select.where(where)).count()

        self.menu.add_row_button(
            text=button.get_processed_title(amount=amount),
            path="../".join(("" for _ in range(back_step + 1))) + button.path,
        )

    def _add_row_many_buttons(self, buttons: Iterable[ButtonData], back_step: int = 0):
        buttons_data = [
            (
                btn.get_processed_title(),
                "../".join(("" for _ in range(back_step + 1))) + btn.path,
            )
            for btn in buttons
        ]
        self.menu.add_row_many_buttons(*buttons_data)

    def categories(self, back_step: int = 0):
        self._add_row_button(
            button=CATEGORIES_BTN,
            model=Category,
            back_step=back_step,
        )

    def sources(self, category_id: int = None, back_step: int = 0):
        self._add_row_button(
            button=SOURCES_BTN,
            model=Source,
            where=(
                ((Source.category_id == category_id) & (Source.is_deleted == False))
                if category_id
                else (Source.is_deleted == False)
            ),
            back_step=back_step,
        )

    def filters(self, source_id: int = None, back_step: int = 0) -> None:
        self._add_row_button(
            button=FILTERS_BTN,
            model=Filter,
            where=Filter.source_id == source_id,
            back_step=back_step,
        )

    def cleanups(self, amount: int = 0, back_step: int = 0) -> None:
        self._add_row_button(
            button=CLEANUPS_BTN,
            amount=amount,
            back_step=back_step,
        )

    def alert_rules(
        self,
        user_id: int,
        category_id: int = None,
        back_step: int = 0,
    ) -> None:
        self._add_row_button(
            button=ALERT_RULES_BTN,
            model=AlertRule,
            where=(AlertRule.user_id == user_id)
            & (AlertRule.category_id == category_id),
            back_step=back_step,
        )

    def options(self, back_step: int = 0):
        self._add_row_button(
            button=OPTIONS_BTN,
            back_step=back_step,
        )

    def read(self, back_step: int = 0):
        self._add_row_button(
            button=READ_BTN,
            back_step=back_step,
        )

    def messages_histories(self, back_step: int = 0):
        self._add_row_button(
            button=MESSAGES_HISTORIES_BTN,
            back_step=back_step,
        )

    def statistics(self, back_step: int = 0):
        self._add_row_button(
            button=STATISTICS_BTN,
            back_step=back_step,
        )

    def filters_histories(self, back_step: int = 0):
        self._add_row_button(
            button=FILTERS_HISTORIES_BTN,
            back_step=back_step,
        )

    def add(self, back_step: int = 0):
        self._add_row_button(
            button=ADD_BTN,
            back_step=back_step,
        )

    def edit(self, back_step: int = 0):
        self._add_row_button(
            button=EDIT_BTN,
            back_step=back_step,
        )

    def delete(self, back_step: int = 0):
        self._add_row_button(
            button=DELETE_BTN,
            back_step=back_step,
        )

    def confirmation_delete(self, back_step: int = 0):
        self._add_row_button(
            button=CONFIRMATION_DELETE_BTN,
            back_step=back_step,
        )

    def row_edit_delete(self, back_step: int = 0):
        self._add_row_many_buttons(
            buttons=(EDIT_MINI_BTN, DELETE_MINI_BTN),
            back_step=back_step,
        )
