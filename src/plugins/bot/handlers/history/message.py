from common.links import get_message_link
from common.text import get_shortened_text
from models import Category, MessageHistory, Source
from plugins.bot import router
from plugins.bot.constants.settings import DEFAULT_NUM_ITEMS_ON_TEXT
from plugins.bot.menu import Menu
from plugins.bot.utils.links import get_channel_formatted_link


@router.page(path=r"/mh/", pagination=True)
async def message_history(menu: Menu):
    query = (
        MessageHistory.select(MessageHistory, Source, Category)
        .join(Source)
        .switch()
        .join(Category)
        .order_by(MessageHistory.id.desc())
    )

    start_text = ""
    if source_id := menu.path.get_value("s"):
        src_link = await get_channel_formatted_link(source_id)
        start_text = f" источника {src_link}"
        query = query.where(Source.id == source_id)
    elif category_id := menu.path.get_value("c"):
        cat_link = await get_channel_formatted_link(category_id)
        start_text = f" категории {cat_link}"
        query = query.where(Category.id == category_id)

    pagination = menu.set_pagination(
        total_items=query.count(),
        size=DEFAULT_NUM_ITEMS_ON_TEXT,
    )

    text_items = []
    for item in query.paginate(pagination.page, pagination.size):
        text_items.append(
            f'{"🏞" if item.source_media_group_id else "🗞"}'
            f'{">📝" if item.edited_at else ""}'
            f'{">🗑" if item.deleted_at else ""}'
            f" [{get_shortened_text(item.source.title, 30)}]"
            f"({get_message_link(item.source_id, item.source_message_id)})\n"
            f'✅{">🖨" if item.category_message_rewritten else ""}'
            f'{">🗑" if item.deleted_at else ""}'
            f" [{get_shortened_text(item.category.title, 30)}]"
            f"({get_message_link(item.category_id, item.category_message_id)})\n"
            f'__{item.source_message_id} {item.created_at.strftime("%Y.%m.%d, %H:%M:%S")}__'
        )

    return (
        f"**История сообщений{start_text}**\n\n"
        + "\n\n".join(text_items)
        + f"\n\nВсего: **{pagination.total_items}**"
    )
