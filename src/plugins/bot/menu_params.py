from plugins.bot.utils.links import get_channel_formatted_link, get_user_formatted_link


async def category(category_id: int) -> tuple[str, str]:
    return "Категория", await get_channel_formatted_link(category_id)


async def source(source_id: int) -> tuple[str, str]:
    return "Источник", await get_channel_formatted_link(source_id)


async def user(user_id: int) -> tuple[str, str]:
    return "Пользователь", await get_user_formatted_link(user_id)
