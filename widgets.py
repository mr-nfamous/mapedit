
from functools import singledispatch

from mapedit import *
from tkinter import Event as _TkEvent
class Widget:
    
    sentinel = object()
    
    def __init__(self, parent, boxtype=Frame, **cfg):
        self.parent = parent
        self.root = parent.root
        self.box = boxtype(self.root, **cfg)
        self.left_is_active = False
        self.right_is_active = False
        self.mouse_moved = False
        
    def grid(self, *rows, **opts):
        self.box.grid(**opts)

    def create_canvas(self, width, height, **opts):
        opts = {**dict(width=width,
                       height=height,
                       highlightthickness=0,
                       border=0),
                **opts}
        return Canvas(self.box, **opts)
    
    @property
    def is_active(self):
        return self.left_is_active or self.right_is_active

class MouseEvent:
    def __init__(self, gx, gy, _event=None):
        self._grid_x, self._grid_y = (gx, gy)
        self.__event = _event

    def tkevent_delta(self, other):
        e = self._event
        return e.x - other._event.x, e.y - other._event.y

    def grid_delta(self, other):
        return self.grid_x - other.grid_x, self.grid_y - other.grid_y
    
    @property
    def _event(self):
        if self.__event:
            return self.__event
        return _event(*self.canvas)

    @property
    def grid_x(self):
        return max(0, min(self._grid_x, settings.map_tile_width-1))

    @property
    def grid_y(self):
        return max(0, min(self._grid_y, settings.map_tile_height-1))
    
    @property
    def grid(self):
        return self.grid_x, self.grid_y
    
    @property
    def canvas_x(self):
        return self.grid_x * 16

    @property
    def canvas_y(self):
        return self.grid_y * 16

    @property
    def canvas(self):
        return (self.grid_x * 16), (self.grid_y * 16)

    def copy(self):
        return type(self)(self.grid_x, self.grid_y, self.__event)
    
    def __reduce__(self):
        return self._rebuild, (bytes(self.grid),)

    @classmethod
    def _rebuild(cls, data):
        return cls(*data)

    def __add__(self, other):
        return type(self)(self.grid_x+other[0], self.grid_y+other[1],
                          self.__event)

    def __iadd__(self, other):
        self.grid_x += other[0]
        self.grid_y += other[1]
        return self

    def __repr__(self):
        return f'{type(self).__name__}{self.grid}'

    def __hash__(self):
        return hash((type(self), self.grid))

    def __eq__(self, other):
        return hash(other) == hash(self)
    
_event = namedtuple('_event', ('x', 'y'))

@singledispatch
def mouse_event(event):
    x = event.x // 16 * 16
    y = event.y // 16 * 16
    return MouseEvent(x, y)

@mouse_event.register(_event)
def _mouse_event(event):
    return MouseEvent(event.x//16, event.y//16, event)

@mouse_event.register(tuple)
def _mouse_event(event):
    return MouseEvent(*event)

@mouse_event.register(int)
def _mouse_event(x, y):
    return MouseEvent(x, y)

@mouse_event.register(_TkEvent)
def _mouse_event(event):
    return MouseEvent(event.x//16, event.y//16, _event(event.x, event.y))

##class MouseEvent:
##    
##    def __init__(self, event, gx, gy, cx, cy):
##        self._event = event
##        self.grid_x, self.grid_y = self.grid = gx, gy
##        self.canvas_x, self.canvas_y = self.canvas = cx, cy
##        
##    def tkevent_delta(self, other):
##        return self._event.x - other._event.x, self._event.y - other._event.y
##    
##    def canvas_delta(self, other):
##        return self.canvas_x - other.canvas_x, self.canvas_y - other.canvas_y
##
##    def grid_delta(self, other):
##        return self.grid_x - other.grid_x, self.grid_y - other.grid_y
##
##    def __hash__(self):
##        return hash((type(self), self.grid))
##
##    def __eq__(self, other):
##        return hash((type(self), self.grid)) == hash(other)
##
##    def _dump(self):
##        data = bytes(self.grid)
##        data+= ((self.canvas_x << 12) + self.canvas_y).to_bytes(3,'little')
##        return data
##
##    def __matmul__(self, other):
##        x, y, xo, yo, mbw, mbh = other
##        x = max(0, min(self._event.x + x * 16, mbw))
##        y = max(0, min(self._event.y + y * 16, mbh))
##        return mouse_event(_SimpleMouseEvent(x, y), xo, yo, mbw-1, mbh-1)
##
##    def __imatmul__(self, other):
##        new = self.__matmul__(other)
##        self._event = new._event
##        self.grid_x, self.grid_y = self.grid = new.grid
##        self.canvas_x, self.canvas_y = self.canvas = new.canvas
##        return self
##
##    def __reduce__(self):
##        data = b''.join(i.to_bytes(1,'little') for i in self.grid)
##        data+= ((self.canvas_x << 12) + self.canvas_y).to_bytes(3, 'little')
##        return self._rebuild, (data,)
##
##    @classmethod
##    def _rebuild(cls, data):
##        gx, gy = data[:2]
##        c = int.from_bytes(data[2:],'little')
##        cx = c >> 12
##        cy = c & 4095
##        return cls(_SimpleMouseEvent(cx, cy), gx, gy, cx, cy)
##
##    def __repr__(self):
##        t = type(self)
##        name = f'{t.__module__}.{t.__name__}'
##        return f'<{name} grid={self.grid} canvas={self.canvas}>'
##    
##class _SimpleMouseEvent:
##    def __init__(self, x, y):
##        self.x = x
##        self.y = y
##        
##@functools.singledispatch
##def mouse_event(event, xoffset=0, yoffset=0, maxwidth =None, maxheight=None):
##    
##    x = max(0, min(event.x, maxwidth))
##    y = max(0, min(event.y, maxheight))
##    gx = x//settings.tile_size + xoffset
##    gy = y//settings.tile_size + yoffset
##    cx = gx * settings.tile_size
##    cy = gy * settings.tile_size
##    return MouseEvent(event, gx, gy, cx, cy)
##
##@mouse_event.register(_TkEvent)
##def _mouse_event(event, xoffset=0, yoffset=0, maxwidth=None, maxheight=None):
##    event = _SimpleMouseEvent(event.x, event.y)
##    return mouse_event(event, xoffset, yoffset, maxwidth, maxheight)
##
##@mouse_event.register(tuple)
##def _mouse_event(event, xoffset=0, yoffset=0, maxwidth=None, maxheight=None):
##    event = _SimpleMouseEvent(*event)
##    return mouse_event(event, xoffset, yoffset, maxwidth, maxheight)
##
##@mouse_event.register(MouseEvent)
##def _mouse_event(event, xoffset=0, yoffset=0, maxwidth=None, maxheight=None):
##    return mouse_event(event._event, xoffset, yoffset, maxwidth, maxheight)
    
def make_cell_highlight_box(w, h):
    if w > 100 or h > 100:
        print(f'MAKE CELL HIGHLIGHT BOX {w*16} x {h*16} IS TOO BIG')
    cell_highlight = Image.new('RGBA', (16, 16))
    pix = cell_highlight.load()
    for i in range(8):
        a = int(212 * 0.825 ** i) + int(i * ((8 + i)/(8 * 1.5)))
        for s in ((i, 0), (i, 15), (15-i, 0), (15-i, 15)):
            pix[s] = pix[s[::-1]] =(0, 0, 0, a)
    grid = Image.new('RGBA', (w*16, h*16))
    for x in range(0, w*16, 16):
        for y in range(0, h*16, 16):
            grid.paste(cell_highlight, (x, y), cell_highlight)
    return grid

def make_checkerboard(w, h):
    #666666 # 999999
    dark = Image.new('RGBA', (16, 16), (102, 102, 102, 255))
    lite = Image.new('RGBA', (16, 16), (153, 153, 153, 255))
    bg = Image.new('RGBA', (w*16, h*16))
    for x in range(w):
        for y in range(h):
            i = dark if (x+y)%2 else lite
            bg.paste(i, (x*16,  y*16), i)
    return bg
