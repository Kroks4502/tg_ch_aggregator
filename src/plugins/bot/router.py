import inspect
from functools import wraps
from typing import Callable, Optional

import pyrogram
from pyrogram.handlers import CallbackQueryHandler, MessageHandler

from common.senders import send_message_to_admins
from plugins.bot.menu import Menu
from utils import custom_filters
from utils.input_wait_manager import InputWaitManager


class CallbackQueryRouter:
    def __init__(self, client: "pyrogram.Client", input_wait_manager: InputWaitManager):
        self.client = client
        self.input_wait_manager = input_wait_manager

    def page(
        self,
        *,
        path: str = "/",
        back_step: int = 1,
        pagination: bool = False,
        admin_only: bool = True,
        send_to_admins: bool = False,
        reply: bool = False,
        add_wait_for_input: Callable = None,
        callback_answer_text: str = None,
        group: int = 0,
        command: bool = False,
    ):
        """
        Декоратор для организации меню путём обработки запросов обратного вызова,
        используя ~pyrogram.handlers.CallbackQueryHandler.

        Обернутая функция может принимать следующие аргументы:

        - client: Client
        - menu: Menu
        - callback_query: CallbackQuery

        Она должна возвращать текст сообщения для пользователя или None, когда ответ не требуется.

        :param path: Путь меню.
        :param back_step: Количество шагов для кнопки назад.
        :param pagination: Добавить пагинацию.
        :param admin_only: Доступно только администраторам.
        :param send_to_admins: Отправить сообщение администраторам.
        :param reply: Ответить репликой.
        :param add_wait_for_input: Добавить функцию ожидающую ввод от пользователя.
        :param callback_answer_text: Текст для метода answer of ~pyrogram.pyrogram.types.CallbackQuery.
        :param group: Группа обработчика.
        :param command: Подключить обработку командами.
        """
        origin_path = path
        if pagination:
            path += r"(p/\d+/|)"
        path += r"(\?new|)$"

        filters = pyrogram.filters.regex(pattern=path)
        if admin_only:
            filters &= custom_filters.admin_only

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner(
                client: "pyrogram.Client",
                callback_query: "pyrogram.types.CallbackQuery",
                **kwargs,
            ):
                if callback_query.id is not ...:
                    await callback_query.answer(text=callback_answer_text)

                menu = Menu(
                    path=callback_query.data,
                    user=callback_query.from_user,
                    back_step=back_step,
                )

                text = await func(
                    **self._get_func_kwargs(
                        func,
                        available_kwargs=dict(
                            client=client,
                            menu=menu,
                            callback_query=callback_query,
                        ),
                    ),
                    **kwargs,
                )

                await self._send_final_text(
                    event=callback_query,
                    reply=menu.need_send_new_message or reply,
                    markup=(
                        None
                        if reply and not menu.need_send_new_message
                        else menu.reply_markup
                    ),
                    text=text,
                )

                await self._send_message_to_admins(
                    send_to_admins,
                    callback_query.from_user,
                    text,
                )
                await self._add_to_input_wait_manager(
                    add_wait_for_input,
                    callback_query,
                )

            self.client.add_handler(
                handler=CallbackQueryHandler(
                    callback=inner,
                    filters=filters,
                ),
                group=group,
            )

            if command:
                self._page_as_command(
                    func=func,
                    path=origin_path,
                    back_step=back_step,
                    group=group,
                    admin_only=admin_only,
                )

            return inner

        return decorator

    def wait_input(
        self,
        *,
        back_step: int = 1,
        send_to_admins: bool = False,
        add_wait_for_input: Callable = None,
        initial_text: str = None,
        delete_previous_menu: bool = True,
    ):
        """
        Декоратор для создания обработчика сообщения от пользователя,
        используя ~pyrogram.handlers.MessageHandler.

        Функция может принимать следующие аргументы:

        - client: Client
        - menu: Menu
        - message: Message

        Функция должна возвращать текст сообщения для пользователя.

        :param back_step: Количество шагов для кнопки назад.
        :param send_to_admins: Отправить сообщение администраторам.
        :param add_wait_for_input: Добавить функцию ожидающую ввод от пользователя.
        :param initial_text: Первоначальный текст ответа.
        :param delete_previous_menu: Удалить предыдущее сообщение с меню.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner(
                client: "pyrogram.Client",
                message: "pyrogram.types.Message",
                callback_query: "pyrogram.types.CallbackQuery",
            ):
                answer_message = None
                if initial_text:
                    answer_message = await message.reply_text(initial_text)

                menu = Menu(
                    path=callback_query.data,
                    user=callback_query.from_user,
                    back_step=back_step,
                )

                try:
                    text = await func(
                        **self._get_func_kwargs(
                            func,
                            available_kwargs=dict(
                                client=client,
                                menu=menu,
                                message=message,
                            ),
                        )
                    )
                except ValueError as error:
                    text = str(error)
                else:
                    await self._send_message_to_admins(
                        send_to_admins,
                        callback_query.from_user,
                        text,
                    )
                    await self._add_to_input_wait_manager(
                        add_wait_for_input,
                        callback_query,
                    )

                await self._send_final_text(
                    event=answer_message or message,
                    reply=not answer_message,
                    markup=menu.reply_markup,
                    text=text,
                )

                if delete_previous_menu:
                    await callback_query.message.delete()

            return inner

        return decorator

    def _page_as_command(
        self,
        func: Callable,
        path: str,
        back_step: int,
        group: int,
        admin_only: bool,
    ):
        """
        :param func: Функция для обработчика.
        :param path: Путь меню.
        :param back_step: Количество шагов для кнопки назад.
        :param group: Группа обработчика.
        :param admin_only: Доступно только администраторам.
        """

        async def inner(
            client: "pyrogram.Client",
            message: "pyrogram.types.Message",
        ):
            msg_path = message.text.replace("_", "/") + "/"
            menu = Menu(
                path=msg_path,
                user=message.from_user,
                back_step=back_step,
            )
            menu.set_footer_buttons = False

            try:
                text = await func(
                    **self._get_func_kwargs(
                        func,
                        available_kwargs=dict(
                            client=client,
                            menu=menu,
                            message=message,
                        ),
                    )
                )
            except ValueError as error:
                text = str(error)

            await self._send_final_text(
                event=message,
                reply=True,
                text=text,
                markup=menu.reply_markup,
            )

        commands = [path.strip("/").replace("/", "_")]
        filters = pyrogram.filters.command(commands)
        if admin_only:
            filters &= custom_filters.admin_only

        self.client.add_handler(
            handler=MessageHandler(
                callback=inner,
                filters=filters,
            ),
            group=group,
        )

    def command(
        self,
        *,
        commands: str | list[str],
        group: int = 0,
    ):
        """
        Декоратор для создания обработчика команд от пользователя,
        используя ~pyrogram.handlers.MessageHandler.

        Функция может принимать следующие аргументы:

        - client: Client
        - menu: Menu
        - message: Message

        Функция должна возвращать текст сообщения для пользователя.

        :param commands: Список обрабатываемых команд.
        :param group: Группа обработчика.
        """

        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def inner(
                client: "pyrogram.Client",
                message: "pyrogram.types.Message",
            ):
                menu = Menu(
                    path="/",
                    user=message.from_user,
                )

                try:
                    text = await func(
                        **self._get_func_kwargs(
                            func,
                            available_kwargs=dict(
                                client=client,
                                menu=menu,
                                message=message,
                            ),
                        )
                    )
                except ValueError as error:
                    text = str(error)

                await self._send_final_text(
                    event=message,
                    reply=True,
                    text=text,
                    markup=menu.reply_markup,
                )

            self.client.add_handler(
                handler=MessageHandler(
                    callback=inner,
                    filters=pyrogram.filters.command(commands),
                ),
                group=group,
            )

            return inner

        return decorator

    @staticmethod
    def _get_func_kwargs(func: Callable, available_kwargs: dict):
        return {
            arg_name: available_kwargs[arg_name]
            for arg_name in inspect.signature(func).parameters
            if arg_name in available_kwargs
        }

    async def _add_to_input_wait_manager(
        self,
        add_wait_for_input: Callable,
        callback_query: "pyrogram.types.CallbackQuery",
    ):
        if add_wait_for_input:
            self.input_wait_manager.add(
                callback_query.message.chat.id,
                add_wait_for_input,
                self.client,
                callback_query,
            )

    async def _send_final_text(
        self,
        event: ["pyrogram.types.Message", "pyrogram.types.CallbackQuery"],
        reply: bool,
        text: str,
        markup: Optional["pyrogram.types.InlineKeyboardMarkup"],
    ):
        if text:
            if reply:
                await self.client.send_message(
                    chat_id=event.from_user.id,
                    text=text,
                    reply_markup=markup,
                    disable_web_page_preview=True,
                )
            else:
                message = (
                    event
                    if isinstance(event, pyrogram.types.Message)
                    else event.message
                )

                if message is None:
                    raise ValueError("_send_final_text: not message for edit")

                await self.client.edit_message_text(
                    chat_id=message.from_user.id,
                    message_id=message.id,
                    text=text,
                    reply_markup=markup,
                    disable_web_page_preview=True,
                )

    async def _send_message_to_admins(
        self,
        send_to_admins: bool,
        user: "pyrogram.types.User",
        text: str,
    ):
        if send_to_admins and text:
            await send_message_to_admins(
                client=self.client,
                text=f"Действие пользователя {self._get_username(user)}\n\n{text}",
                except_user_id=user.id,
            )

    @staticmethod
    def _get_username(user: "pyrogram.types.User") -> str:
        """Получить имя пользователя для сообщения администраторам."""
        if user.username:
            return f"@{user.username}"

        full_name = (
            f'{user.first_name + " " if user.first_name else ""}'
            f'{user.last_name if user.last_name else ""}'
        )
        return f"{full_name} ({user.id})" if full_name else f"{user.id}"
