from utils.menu.abstract import MenuAbstract


class ButtonAdderBase:
    def __init__(self, menu: MenuAbstract):
        self.menu = menu
