import re
import urllib.parse


class Path:
    """Построение путей в меню бота для callback_query.data."""

    def __init__(self, path: str):
        self.path = path

    def get_prev(self, step: int = 1) -> str:
        result = self._search_first_group(
            r'([\w/:-]*/)([\w/:-]*/){' + str(step) + r'}$'
        )
        return result or '/'

    def get_value(self, prefix: str) -> int | None:
        try:
            return int(
                self._search_first_group(r'/' + prefix + r'/([\d-]+)/', self.path)
            )
        except ValueError:
            return None

    def _search_first_group(self, pattern: str, path: str = '') -> str:
        path = self.path if not path else path
        match = re.search(pattern, path)
        if match:
            return match.group(1)
        return ''

    def join(self, path: str | int) -> str:
        path_join = urllib.parse.urljoin(self.path, path)
        if path_join.endswith('/'):
            return path_join

        return path_join + '/'

    def __str__(self):
        return self.path
