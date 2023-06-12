from clients import user
from models import Source


async def get_chat_warnings(source_obj: Source) -> str:
    chat = await user.get_chat(source_obj.tg_id)
    text = []
    if chat.is_verified:
        text.append(f'Проверен: {chat.is_verified} ✅')

    if chat.is_restricted:
        text.append(f'Ограничен: {chat.is_restricted} 🔺')

    if chat.is_scam:
        text.append(f'Мошенник: {chat.is_scam} 🔺')

    if chat.is_fake:
        text.append(f'Фейк: {chat.is_fake} 🔺')

    if chat.has_protected_content:
        text.append(
            f'Запрет пересылки: {chat.has_protected_content} '
            + ('✅' if source_obj.is_rewrite else '⚠')
        )

    return '\n'.join(text)
