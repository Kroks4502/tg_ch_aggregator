from pyrogram import Client, filters
from pyrogram.types import CallbackQuery

from models import Filter, Source
from plugins.bot.utils.chat_info import get_chat_info
from plugins.bot.utils.checks import is_admin
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/s/-\d+/$'),
)
async def detail_source(_, callback_query: CallbackQuery):
    await callback_query.answer()

    menu = Menu(callback_query.data)

    source_id = menu.path.get_value('s')
    source_obj: Source = Source.get(source_id)

    last_text = []
    if is_admin(callback_query.from_user.id):
        menu.add_row_many_buttons(
            ('Категория', ':edit'),
            ('Название', ':edit_alias'),
        )

        menu.add_row_many_buttons(
            (
                'Сменить режим',
                ':off_rewrite' if source_obj.is_rewrite else ':on_rewrite',
            ),
            ('Удалить', ':delete'),
        )

        menu.add_row_button('📖 История сообщений', 'mh')

        ft_count = Filter.select().where(Filter.source == source_obj).count()
        menu.add_row_button('🪤 Фильтры' + (f' ({ft_count})' if ft_count else ''), 'ft')

        if source_obj.is_rewrite:
            cl_count = len(source_obj.cleanup_list)
            menu.add_row_button(
                '🧹 Очистка' + (f' ({cl_count})' if cl_count else ''), 'cl'
            )

        chat_info = await get_chat_info(source_obj)
        if chat_info:
            last_text.append(f"{chat_info}\n")

    if source_obj.title_alias:
        last_text.append(f'Название: **{source_obj.title_alias}**')

    last_text.append(
        'Режим перепечатывания: ' + ('✅' if source_obj.is_rewrite else '📴')
    )

    text = await menu.get_text(source_obj=source_obj, last_text='\n'.join(last_text))
    await callback_query.message.edit_text(
        text=text,
        reply_markup=menu.reply_markup,
        disable_web_page_preview=True,
    )
