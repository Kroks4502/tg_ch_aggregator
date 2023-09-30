def alias(value: str):
    return "Псевдоним", value or "< отсутствует >"


def rewrite(is_rewrite: bool):
    return "Перепечатывание", "on" if is_rewrite else "off"
