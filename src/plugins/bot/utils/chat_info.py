from async_lru import alru_cache

from clients import telethon_user_client
from models import Source


@alru_cache(maxsize=256)
async def get_chat_info(source_obj: Source) -> str:
    entity = await telethon_user_client.get_entity(source_obj.id)
    text = []

    if getattr(entity, "verified", False):
        text.append(f"Проверен: True ✅")

    if getattr(entity, "restricted", False):
        text.append(f"Ограничен: True 🔺")

    if getattr(entity, "scam", False):
        text.append(f"Мошенник: True 🔺")

    if getattr(entity, "fake", False):
        text.append(f"Фейк: True 🔺")

    # Telethon: noforwards = нет пересылки (pyrogram: has_protected_content)
    if getattr(entity, "noforwards", False):
        text.append(
            f"Запрет пересылки: True "
            + ("✅" if source_obj.is_rewrite else "⚠")
        )

    return "\n".join(text)
