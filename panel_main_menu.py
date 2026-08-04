# ux home — the top of the nested U1 menu tree, rendered as big flat tiles.
# Home IS the top-level menu (Print / Prepare / Settings / Infinity Flow); every
# other screen is a drill-down from here with native KlipperScreen back. A thin
# subclass of the menu panel: it inherits the tile rendering (2-col fill,
# expand_last, big fonts) so the whole tree looks and behaves identically.
from panels.menu import Panel as MenuPanel


class Panel(MenuPanel):
    pass
