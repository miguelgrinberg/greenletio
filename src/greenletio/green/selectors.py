from greenletio.green import select as green_select
from greenletio.patcher import copy_globals
import selectors as _original_selectors_

copy_globals(_original_selectors_, globals())


class SelectSelector(_original_selectors_.SelectSelector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._select = green_select.select


DefaultSelector = SelectSelector
