import inspect
import logging
import re
from typing import Awaitable, Callable

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    Message,
    User as AiogramUser,
)

from common.dto import AdminNotification
from common.notifier_registry import get_admin_notifier
from plugins.bot.fsm import WaitInput
from plugins.bot.menu import Menu
from plugins.bot.middlewares.admin import AdminOnlyMiddleware
from plugins.bot.wait_registry import make_key, register, resolve

logger = logging.getLogger(__name__)


def _suffix_optional_pagination_and_new(path: str, pagination: bool) -> str:
    if pagination:
        path += r"(p/\d+/|)"
    path += r"(\?new|)$"
    return path


class CallbackQueryRouter:
    """
    Совместимая надстройка над aiogram.Router/Dispatcher: сохраняет старые
    декораторы @router.page / @router.wait_input / @router.command, чтобы
    handler'ы могли мигрировать без перерегистрации.
    """

    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

        # Два sub-router'а: один защищён admin-middleware, второй — публичный.
        self.admin_router = Router(name="bot.admin")
        self.admin_router.callback_query.middleware(AdminOnlyMiddleware())
        self.admin_router.message.middleware(AdminOnlyMiddleware())

        self.public_router = Router(name="bot.public")

        dispatcher.include_router(self.public_router)
        dispatcher.include_router(self.admin_router)

        # Универсальный handler ожидания текстового ввода (FSM).
        self.public_router.message.register(
            self._handle_wait_input,
            StateFilter(WaitInput.waiting_text),
        )

    # ------------------------------------------------------------------ page

    def page(
        self,
        *,
        path: str,
        back_step: int = 1,
        pagination: bool = False,
        admin_only: bool = True,
        send_to_admins: bool = False,
        reply: bool = False,
        add_wait_for_input: Callable | None = None,
        callback_answer_text: str | None = None,
        group: int = 0,
        command: bool = False,
    ):
        """См. оригинальный CallbackQueryRouter.page — параметры совпадают."""
        origin_path = path
        regex = _suffix_optional_pagination_and_new(path, pagination)
        compiled = re.compile(regex)

        target_router = self.admin_router if admin_only else self.public_router

        def decorator(func: Callable) -> Callable:
            async def inner(callback_query: CallbackQuery, state: FSMContext):
                if callback_query.id != "synthetic":
                    try:
                        await callback_query.answer(text=callback_answer_text)
                    except TelegramBadRequest:
                        # callback_query истёк — не критично, продолжаем
                        pass

                menu = Menu(
                    path=callback_query.data,
                    user_id=callback_query.from_user.id,
                    back_step=back_step,
                )

                text = await func(
                    **_pick_kwargs(
                        func,
                        dict(
                            bot=callback_query.bot,
                            client=callback_query.bot,
                            menu=menu,
                            callback_query=callback_query,
                        ),
                    )
                )

                await _send_final_text(
                    bot=callback_query.bot,
                    event=callback_query,
                    reply=menu.need_send_new_message or reply,
                    markup=(
                        None
                        if reply and not menu.need_send_new_message
                        else menu.reply_markup
                    ),
                    text=text,
                )

                if send_to_admins and text:
                    await _send_to_admins(callback_query.from_user, text)

                if add_wait_for_input:
                    await _arm_wait_input(
                        state=state,
                        func=add_wait_for_input,
                        callback_path=callback_query.data,
                    )

            inner.__name__ = func.__name__
            inner.__qualname__ = func.__qualname__
            inner.__module__ = func.__module__

            # search-режим: схема путей у нас «хвостовая» (`/s/` должен
            # матчить `/c/-123/s/`), а default mode у magic_filter — match,
            # т.е. привязка к началу строки. Это бы рубило все вложенные
            # переходы вроде «Категории → выбор категории → Источники».
            target_router.callback_query.register(
                inner, F.data.regexp(compiled, mode="search")
            )

            if command:
                self._page_as_command(
                    func=func,
                    path=origin_path,
                    back_step=back_step,
                    admin_only=admin_only,
                )

            return inner

        return decorator

    # ------------------------------------------------------------ wait_input

    def wait_input(
        self,
        *,
        back_step: int = 1,
        send_to_admins: bool = False,
        add_wait_for_input: Callable | None = None,
        initial_text: str | None = None,
        delete_previous_menu: bool = True,
    ):
        """
        Регистрирует функцию-обработчик текстового ввода в wait_registry.
        Сама функция не превращается в aiogram-handler — её вызовет
        универсальный FSM-handler из __init__.
        """

        def decorator(func: Callable) -> Callable:
            # Метаданные оригинальной функции для FSM-handler'а
            func.__wait_input_meta__ = dict(
                back_step=back_step,
                send_to_admins=send_to_admins,
                add_wait_for_input=add_wait_for_input,
                initial_text=initial_text,
                delete_previous_menu=delete_previous_menu,
            )
            register(func)
            return func

        return decorator

    # --------------------------------------------------------------- command

    def command(
        self,
        *,
        commands: str | list[str],
        group: int = 0,
    ):
        """См. оригинальный CallbackQueryRouter.command."""
        cmd_list = [commands] if isinstance(commands, str) else list(commands)

        def decorator(func: Callable) -> Callable:
            async def inner(message: Message, state: FSMContext):
                # Команды /start и /cancel сбрасывают FSM
                await state.clear()

                menu = Menu(path="/", user_id=message.from_user.id)

                try:
                    text = await func(
                        **_pick_kwargs(
                            func,
                            dict(
                                bot=message.bot,
                                client=message.bot,
                                menu=menu,
                                message=message,
                            ),
                        )
                    )
                except ValueError as error:
                    text = str(error)

                await _send_final_text(
                    bot=message.bot,
                    event=message,
                    reply=True,
                    markup=menu.reply_markup,
                    text=text,
                )

            inner.__name__ = func.__name__
            inner.__qualname__ = func.__qualname__
            inner.__module__ = func.__module__

            self.public_router.message.register(inner, Command(*cmd_list))
            return inner

        return decorator

    # ------------------------------------------------------------- internals

    def _page_as_command(
        self,
        func: Callable,
        path: str,
        back_step: int,
        admin_only: bool,
    ):
        """
        Открывает страницу меню по команде /a_b при path=/a/b/.
        """
        cmd_name = path.strip("/").replace("/", "_")
        target_router = self.admin_router if admin_only else self.public_router

        async def inner(message: Message, state: FSMContext):
            await state.clear()

            msg_path = message.text.replace("_", "/") + "/"
            menu = Menu(
                path=msg_path,
                user_id=message.from_user.id,
                back_step=back_step,
            )
            menu.set_footer_buttons = False

            try:
                text = await func(
                    **_pick_kwargs(
                        func,
                        dict(
                            bot=message.bot,
                            client=message.bot,
                            menu=menu,
                            message=message,
                        ),
                    )
                )
            except ValueError as error:
                text = str(error)

            await _send_final_text(
                bot=message.bot,
                event=message,
                reply=True,
                text=text,
                markup=menu.reply_markup,
            )

        target_router.message.register(inner, Command(cmd_name))

    async def _handle_wait_input(
        self,
        message: Message,
        state: FSMContext,
    ):
        data = await state.get_data()
        handler_key = data.get("wait_handler_key")
        callback_path = data.get("wait_callback_path", "/")
        meta = data.get("wait_meta") or {}

        func = resolve(handler_key) if handler_key else None
        if func is None:
            await state.clear()
            logger.warning("FSM waiting state has no resolvable handler")
            return

        # Initial-ack: «⏳ Создаю…» и т.п.
        answer_message: Message | None = None
        initial_text = meta.get("initial_text")
        if initial_text:
            answer_message = await message.reply(text=initial_text)

        menu = Menu(
            path=callback_path,
            user_id=message.from_user.id,
            back_step=meta.get("back_step", 1),
        )

        try:
            text = await func(
                **_pick_kwargs(
                    func,
                    dict(
                        bot=message.bot,
                        client=message.bot,
                        menu=menu,
                        message=message,
                    ),
                )
            )
        except ValueError as error:
            text = str(error)
            send_to_admins = False
            next_wait = None
        else:
            send_to_admins = meta.get("send_to_admins", False)
            next_wait = meta.get("add_wait_for_input")

        await state.clear()

        await _send_final_text(
            bot=message.bot,
            event=answer_message or message,
            reply=not answer_message,
            markup=menu.reply_markup,
            text=text,
        )

        if send_to_admins and text:
            await _send_to_admins(message.from_user, text)

        if next_wait:
            await _arm_wait_input(
                state=state,
                func=next_wait,
                callback_path=callback_path,
            )

        if meta.get("delete_previous_menu") and callback_path:
            # Сообщение с меню — последнее сообщение бота до текста пользователя.
            # В исходном коде удалялось callback_query.message.delete(); в aiogram
            # без явного callback_query это сделать сложно, поэтому пропускаем
            # удаление здесь — следующее меню придёт новым сообщением.
            pass


# ============================================================ module-level helpers


def _pick_kwargs(func: Callable, available: dict) -> dict:
    sig = inspect.signature(func)
    return {name: available[name] for name in sig.parameters if name in available}


async def _arm_wait_input(
    state: FSMContext,
    func: Callable[..., Awaitable],
    callback_path: str,
):
    key = make_key(func)
    meta = getattr(func, "__wait_input_meta__", None) or {}
    serializable_meta = {
        "back_step": meta.get("back_step", 1),
        "send_to_admins": meta.get("send_to_admins", False),
        "initial_text": meta.get("initial_text"),
        "delete_previous_menu": meta.get("delete_previous_menu", True),
    }

    nxt = meta.get("add_wait_for_input")
    if nxt is not None:
        serializable_meta["add_wait_for_input"] = make_key(nxt)

    await state.update_data(
        wait_handler_key=key,
        wait_callback_path=callback_path,
        wait_meta=serializable_meta,
    )
    await state.set_state(WaitInput.waiting_text)


async def _send_final_text(
    bot: Bot,
    event: CallbackQuery | Message,
    reply: bool,
    text: str | None,
    markup: InlineKeyboardMarkup | None,
):
    if not text:
        return

    if reply:
        target_chat_id = (
            event.from_user.id if isinstance(event, CallbackQuery) else event.chat.id
        )
        await bot.send_message(
            chat_id=target_chat_id,
            text=text,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
        return

    if isinstance(event, CallbackQuery):
        message = event.message
        if message is None:
            raise ValueError("_send_final_text: callback_query has no message")
        target_chat_id = message.chat.id
        target_message_id = message.message_id
    else:
        target_chat_id = event.chat.id
        target_message_id = event.message_id

    try:
        await bot.edit_message_text(
            chat_id=target_chat_id,
            message_id=target_message_id,
            text=text,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
    except TelegramBadRequest as exc:
        if "message is not modified" in str(exc).lower():
            return
        raise


async def _send_to_admins(user: AiogramUser, text: str):
    """Транслировать сообщение от лица пользователя всем остальным админам."""
    await get_admin_notifier().notify(
        AdminNotification(
            text=f"Действие пользователя {_get_username(user)}\n\n{text}",
            except_user_id=user.id,
        )
    )


def _get_username(user: AiogramUser) -> str:
    if user.username:
        return f"@{user.username}"

    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
    return f"{full_name} ({user.id})" if full_name else f"{user.id}"
