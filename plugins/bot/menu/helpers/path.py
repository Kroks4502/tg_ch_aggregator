import re


class Path:
    def __init__(self, path: str):
        self.path = path

    @property
    def action(self) -> str:
        return self._search_first_group(r':(\w+)/')

    @property
    def section(self) -> str:
        return self._search_first_group(r'^/(\w+)/')

    def add_value(self, prefix: str, value: str | int) -> str:
        return f'{self.path}{prefix}_{value}/'

    def add_action(self, name: str) -> str:
        return f'{self.path}:{name}/'

    def get_prev(self, step: int = 1) -> str:
        return self._search_first_group(
            r'([\w/:]*/)([\w/:]*/){' + str(step) + r'}$')

    def get_value(self, prefix: str, after_action: bool = False) -> str:
        path = (self._get_action_path() if after_action
                else self._get_begin_path())
        return self._search_first_group(r'/' + prefix + r'_(\w+)/', path)

    @property
    def with_confirmation(self):
        return bool(self._search_match('//'))

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

    def __add__(self, other: str) -> str:
        if other[-1] != '/':
            return self.path + other + '/'
        return self.path + other

    def __str__(self):
        return self.path
