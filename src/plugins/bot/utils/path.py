import re
import urllib.parse


class Path:
    """Построение путей в меню бота для callback_query.data."""

    def __init__(self, path: str):
        self.path = path

    @property
    def action(self) -> str:
        return self._search_first_group(r':(\w+)/')

    # def add(self, path: str | int) -> str:
    #     return f'{self.path}{path}/'

    def add_action(self, name: str | int) -> str:
        return f'{self.path}:{name}/'

    def get_prev(self, step: int = 1) -> str:
        result = self._search_first_group(r'([\w/:]*/)([\w/:]*/){' + str(step) + r'}$')
        return result or '/'

    def get_value(self, prefix: str) -> int | None:
        try:
            return int(self._search_first_group(r'/' + prefix + r'/(\d+)/', self.path))
        except ValueError:
            return None

    def _search_first_group(self, pattern: str, path: str = '') -> str:
        path = self.path if not path else path
        match = re.search(pattern, path)
        if match:
            return match.group(1)
        return ''

    def _get_begin_path(self) -> str:
        return self._search_match(r'^/[\w*/]*')

    def _get_action_path(self) -> str:
        return self._search_match(r':[\w*/]*')

    def _search_match(self, pattern: str) -> str:
        match = re.search(pattern, self.path)
        if match:
            return match[0]
        return ''

    def join(self, path: str | int) -> str:
        return urllib.parse.urljoin(self.path, path) + '/'

    # def __add__(self, other: str | int) -> str:
    #     other = str(other)
    #     if not other.endswith('/'):
    #         return f'{self.path}{other}/'
    #     return self.path + other

    def __str__(self):
        return self.path
