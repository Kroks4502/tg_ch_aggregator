from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Chat, ChatPrivileges, Message

from clients import user
from models import Category
from plugins.bot.utils import custom_filters
from plugins.bot.utils.links import get_channel_formatted_link
from plugins.bot.utils.managers import input_wait_manager
from plugins.bot.utils.menu import Menu


@Client.on_callback_query(
    filters.regex(r'/c/:add/$') & custom_filters.admin_only,
)
async def add_category(client: Client, callback_query: CallbackQuery):
    await callback_query.answer()
    await callback_query.message.reply(
        'ОК. Ты добавляешь новую категорию, '
        'в которую будут пересылаться сообщения из источников. '
        'Будет создан новый канал-агрегатор.\n\n'
        '**Введи название новой категории:**'
    )

    input_wait_manager.add(
        callback_query.message.chat.id,
        add_category_waiting_input,
        client,
        callback_query,
    )


async def add_category_waiting_input(
    client: Client,
    message: Message,
    callback_query: CallbackQuery,
):
    menu = Menu(callback_query.data)

    new_channel_name = f'{message.text} | Aggregator'
    new_message = await message.reply_text(f'⏳ Создаю канал «{new_channel_name}»…')

    async def reply(text):
        await new_message.edit_text(
            text,
            reply_markup=menu.reply_markup,
            disable_web_page_preview=True,
        )
        # Удаляем предыдущее меню
        await callback_query.message.delete()

    if len(message.text) > 80:
        await reply('❌ Название категории не должно превышать 80 символов')
        return

    new_channel: Chat = await user.create_channel(
        new_channel_name,
        f'Создан ботом {client.me.username}',
    )

    await new_channel.promote_member(
        client.me.id,
        ChatPrivileges(
            can_manage_chat=True,
            can_delete_messages=True,
            can_manage_video_chats=True,
            can_promote_members=True,
            can_change_info=True,
            can_post_messages=True,
            can_edit_messages=True,
            can_invite_users=True,
        ),
    )

    category_obj: Category = Category.create(
        id=new_channel.id,
        title=new_channel.title,
    )
    cat_link = await get_channel_formatted_link(category_obj.id)
    await reply(f'✅ Категория **{cat_link}** создана')
