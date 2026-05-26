"""
Адаптер pyrogram-flavored Markdown → Telegram HTML.

Зачем: тексты в проекте писались под pyrogram (``**bold**``, ``` `code` ```,
``[text](url)``, и т.п.), который имеет свой диалект Markdown, не совпадающий
ни с одним из двух parse_mode Telegram Bot API (``Markdown`` legacy и
``MarkdownV2``). После миграции бота на aiogram эти тексты стали
отображаться дословно.

Чтобы не переписывать ~40+ шаблонов руками, конвертация делается на лету
перед отправкой/редактированием сообщения. Bot создаётся с
``parse_mode=ParseMode.HTML``.

Поддерживаемые конструкции (pyrogram → HTML):
    ``**bold**``       → ``<b>bold</b>``
    ``__italic__``     → ``<i>italic</i>``
    ``--underline--``  → ``<u>underline</u>``
    ``~~strike~~``     → ``<s>strike</s>``
    ``||spoiler||``    → ``<tg-spoiler>spoiler</tg-spoiler>``
    `` ```pre``` ``    → ``<pre>pre</pre>``    (многострочный код)
    `` `code` ``       → ``<code>code</code>`` (inline)
    ``[text](url)``    → ``<a href="url">text</a>``
    ``> цитата``       → ``<blockquote>цитата</blockquote>``

Принципы:
- Содержимое code-блоков (``inline`` и ``pre``) экранируется как HTML,
  но не парсится на остальные правила (там Markdown-разметка должна быть
  буквальной).
- Содержимое ссылки парсится как обычный текст (можно вложить **жирный**).
- URL в ссылке не парсится — подставляется как есть, минимально
  HTML-экранируется (кавычки/амперсанды).
- Всё остальное HTML-экранируется через ``html.escape`` так, что
  безопасно отправлять любые входные строки.
"""

import html
import re

# Многострочный код ```...``` — DOTALL чтобы захватить переводы строк.
_PRE_RE = re.compile(r"```(.*?)```", re.DOTALL)
# Inline-код `...` — backticks без переноса строки внутри.
_CODE_RE = re.compile(r"`([^`]+?)`", re.DOTALL)
# Ссылка [текст](url)
_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
# Bold **...**
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
# Italic __...__ — без захвата соседних подчёркиваний
_ITALIC_RE = re.compile(r"(?<!_)__(?!_)(.+?)(?<!_)__(?!_)", re.DOTALL)
# Underline --...--
_UNDERLINE_RE = re.compile(r"--(.+?)--", re.DOTALL)
# Strikethrough ~~...~~
_STRIKE_RE = re.compile(r"~~(.+?)~~", re.DOTALL)
# Spoiler ||...||
_SPOILER_RE = re.compile(r"\|\|(.+?)\|\|", re.DOTALL)
# Blockquote: строка(и), начинающиеся с "> "
_QUOTE_LINE_RE = re.compile(r"^&gt; ?(.*)$", re.MULTILINE)


def pyrogram_markdown_to_html(text: str | None) -> str | None:
    """
    Сконвертировать строку с pyrogram-Markdown в Telegram HTML.

    None → None (для удобства подстановки в kwarg'и).
    Пустая строка → пустая строка.
    """
    if not text:
        return text

    placeholders: dict[str, str] = {}

    def _stash(value: str) -> str:
        key = f"\x00PLH{len(placeholders)}\x00"
        placeholders[key] = value
        return key

    def _on_pre(match: re.Match) -> str:
        return _stash(f"<pre>{html.escape(match.group(1))}</pre>")

    def _on_code(match: re.Match) -> str:
        return _stash(f"<code>{html.escape(match.group(1))}</code>")

    def _on_link(match: re.Match) -> str:
        # Текст ссылки — допустимо вложение жирного/курсива → парсим рекурсивно.
        # URL — экранируем только кавычки и амперсанд, чтобы атрибут href был валиден.
        inner_text = pyrogram_markdown_to_html(match.group(1))
        url = match.group(2).replace("&", "&amp;").replace('"', "&quot;")
        return _stash(f'<a href="{url}">{inner_text}</a>')

    # 1. Замокаем code-блоки и ссылки заранее — их содержимое не должно
    #    участвовать в остальных подстановках. Порядок важен: pre до code
    #    (тройные backticks приоритетнее одиночных).
    text = _PRE_RE.sub(_on_pre, text)
    text = _CODE_RE.sub(_on_code, text)
    text = _LINK_RE.sub(_on_link, text)

    # 2. Экранируем всё остальное.
    text = html.escape(text)

    # 3. Применяем простые инлайн-маркеры. Уже на escape'нутом тексте,
    #    поэтому в результате никаких внезапных HTML-тегов от пользователя.
    text = _BOLD_RE.sub(r"<b>\1</b>", text)
    text = _ITALIC_RE.sub(r"<i>\1</i>", text)
    text = _UNDERLINE_RE.sub(r"<u>\1</u>", text)
    text = _STRIKE_RE.sub(r"<s>\1</s>", text)
    text = _SPOILER_RE.sub(r"<tg-spoiler>\1</tg-spoiler>", text)

    # 4. Блочная цитата: строки с "> " → <blockquote>. Несколько подряд
    #    объединяются в один блок (Telegram это нормально рендерит).
    text = _QUOTE_LINE_RE.sub(r"<blockquote>\1</blockquote>", text)

    # 5. Возвращаем placeholder'ы на место.
    for key, value in placeholders.items():
        text = text.replace(key, value)

    return text
