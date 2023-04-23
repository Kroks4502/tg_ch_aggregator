from pyrogram import utils


def get_message_link(chat_id: int, message_id: int):
    return f'https://t.me/c/{utils.get_channel_id(chat_id)}/{message_id}'


def get_shortened_text(text: str, max_len: int, *, last_trim_char: str = '…') -> str:
    if len(text) <= max_len:
        return text

    new_text = ''
    for item in text.split(' '):
        if len(new_text + item) > max_len:
            break
        new_text += f'{item} '

    if new_text:
        return f'{new_text[:-1]}{last_trim_char}'
    return f'{text[:max_len]}{last_trim_char}'
