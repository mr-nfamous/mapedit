
from mapedit.widgets import *
from functools import singledispatch
from collections import namedtuple

class MapCell(deque):
    def __init__(self):
        self.tags = deque()

    def __getitem__(self, item):
        pass

    
class MapAdd:
    def __init__(self, events, tile):
        self.events = events
        self.tile = tile

    def exec(self, instance, stack=None):
        current_map = state.current_map
        z = self.tile.layer
        craise = instance.canvas.tag_raise
        ccreate= instance.canvas.create_image
        for event in self.events:
            cell = current_map[(*event.grid, z)]
            tag = ccreate(event.canvas_x+8, event.canvas_x+8,image=tile.photo)
            cell.append((tile, tag))
            for cell in current_map[event.grid]:
                for t, tag in cell:
                    craise(tag)
        if stack:
            stack.clear()
    
    def __eq__(self, other):
        return (self.events, self.tile) == (other.events, other.tile)

    def __hash__(self):
        return hash((MapAdder, self.events, self.tile))

    def __repr__(self):
        return f'{type(self).__name__}()'

class MapDel:
    def __init__(self, events):
        self.events = events

    def exec(self, instance, stack=None):
        current_map = state.current_map
        cdel = instance.canvas.delete
        for event, tile in events:
            cell = current_map[(*event.grid, tile.layer)]
            tile, tag = cell.pop()
            cdel(tag)
        if stack:
            stack.clear()
    
    def __eq__(self, other):
        return self.events == other.events

    def __hash__(self):
        return hash((MapDel, self.events))

    def __repr__(self):
        return f'{type(self).__name__}()'

class MouseEvent:
    def __init__(self, gx, gy):
        self.grid = self.grid_x, self.grid_y = (gx, gy)

    @property
    def canvas_x(self):
        return self.grid_x * 16

    @property
    def canvas_y(self):
        return self.grid_y * 16

    @property
    def canvas(self):
        return (self.grid_x * 16), (self.grid_y * 16)

    def __reduce__(self):
        return self._rebuild, (bytes(self.grid),)

    @classmethod
    def _rebuild(cls, data):
        return cls(*data)

@singledispatch
def mouse_event(event):
    x = event.x // 16 * 16
    y = event.y // 16 * 16
    return MouseEvent(x, y)

@mouse_event.register(tuple)
def _mouse_event(event):
    return MouseEvent(*event)

@mouse_event.register(int)
def _mouse_event(x, y):
    return MouseEvent(x,y)

