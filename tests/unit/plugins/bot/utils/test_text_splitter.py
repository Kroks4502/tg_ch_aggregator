import src.plugins.bot.utils.text_splitter as text_splitter


def test_split_markdown_preserves_paragraphs(monkeypatch):
    monkeypatch.setattr(
        text_splitter.settings, "TELEGRAM_MAX_TEXT_LENGTH", 11
    )
    text = "aaaaa\n\nbbbbb"
    assert text_splitter.split_markdown(text) == ["aaaaa", "bbbbb"]


def test_split_markdown_aggregates_paragraphs(monkeypatch):
    monkeypatch.setattr(
        text_splitter.settings, "TELEGRAM_MAX_TEXT_LENGTH", 17
    )
    text = "11111\n\n22222\n\n33333"
    assert text_splitter.split_markdown(text) == [
        "11111\n\n22222",
        "33333",
    ]


def test_split_markdown_splits_long_paragraph(monkeypatch):
    monkeypatch.setattr(
        text_splitter.settings, "TELEGRAM_MAX_TEXT_LENGTH", 10
    )
    text = "a" * 25
    assert text_splitter.split_markdown(text) == [
        "a" * 10,
        "a" * 10,
        "a" * 5,
    ]


def test_split_markdown_uses_tg_len(monkeypatch):
    monkeypatch.setattr(
        text_splitter.settings, "TELEGRAM_MAX_TEXT_LENGTH", 3
    )
    text = "🙂a🙂"
    assert text_splitter.split_markdown(text) == ["🙂a", "🙂"]
