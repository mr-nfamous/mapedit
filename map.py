from mapedit import *
from mapedit.widgets import *

class MapAdd:
    def __init__(self, events, tile):
        self.events = events
        self.tile = tile

    def exec(self, instance, stack=None):
        current_map = state.current_map
        z = self.tile.layer
        craise = instance.canvas.tag_raise
        ccreate= instance.canvas.create_image
        tile = self.tile
        photo = tile.photo
        for event in self.events:
            cell = current_map[(*event.grid, z)]
            tag = ccreate(event.canvas_x+8, event.canvas_y+8, image=photo)
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
        for event, tile in self.events:
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
    
class MapBox(Widget):

    def __init__(self, parent):
        mbfs = settings.map_box_frame_size
        super().__init__(parent, height=mbfs, width=mbfs, )
        self.vbar=Scrollbar(self.box, orient='vertical', command=self.yscroll)
        self.hbar=Scrollbar(self.box, orient='horizontal', command=self.xscroll)
        self.canvas = self.create_canvas(mbfs, mbfs)
        self.last_ypos = self.last_xpos = 0
        self.unloaded = Label(self.box,
                              text='Open a map or create a new one...')
        self.unloaded.grid(row=0, column=0, sticky='nsew')
        
    def clickleft(self, event):
        self.left_is_active = True

    def clickright(self, event):
        self.right_is_active = True

    def release(self, event):        
        if not self.mouse_moved:
            self.process_event(event)
        self.left_is_active = self.right_is_active = False
        self.mouse_moved = False

    def motion(self,event):
        if self.is_active:
            self.process_event(event)
            self.mouse_moved = True
        
    def process_event(self, event, *args):
        event = mouse_event(event.x//16+state.map_x_offset,
                            event.y//16+state.map_y_offset)
        if self.left_is_active:
            self.draw(event, tile=state.current_tile)
        elif self.right_is_active:
            self.erase(event)      
        
    def xscroll(self, event, *args):
        if event == 'moveto':
            pos = int(float(args[0]) * settings.map_tile_width)
            if pos != self.last_xpos:
                return self.xscroll('scroll', pos-self.last_xpos, 'units')
        else:
            amount, units = int(args[0]), args[1]
            if units == 'pages':
                amount = amount * settings.map_box_max_tiles - 1
                return self.xscroll('scroll', amount, 'units')
            moved = self.pan(amount, 0)
            if moved:
                self.last_xpos = state.map_x_offset
                self.canvas.xview(event, *args)

    def yscroll(self, event, *args):
        if event == 'moveto':
            pos = int(float(args[0]) * settings.map_tile_height)
            if pos != self.last_ypos:
                return self.yscroll('scroll', pos-self.last_ypos, 'units')
        else:
            y, units = int(args[0]), args[1]
            if units == 'pages':
                y = y * settings.map_box_max_tiles - 1
                return self.yscroll('scroll', y, 'units')
            moved = self.pan(0, y)
            if moved:
                self.last_ypos = state.map_y_offset
                self.canvas.yview(event, *args)

    def move_to_top(self):
        self.canvas.yview('moveto', '0.000')
        state.map_y_offset = 0

    def move_to_left(self):
        self.canvas.xview('moveto', '0.000')
        state.map_x_offset = 0
        
    def pan(self, x, y):
        nx = max(0, min(x + state.map_x_offset, settings.map_box_max_xscroll))
        ny = max(0, min(y + state.map_y_offset, settings.map_box_max_yscroll))
        if nx != state.map_x_offset or ny != state.map_y_offset:
            panned = nx - state.map_x_offset, ny-state.map_y_offset
            state.map_x_offset, state.map_y_offset = nx, ny
            return panned

    def bucket(self, event, tile, clear_redo=True):
        gx, gy = event.grid
        executor = StackItem(bucket, event=event, tile=tile)
        executor.exec(self, stack=state.redo_stack)
        state.stack.append(executor)

    def erase(self, event):
        tile_size = settings.tile_size
        size = state.tool_size - 1
        events = []
        visited = []
        xo, yo = state.map_x_offset, state.map_y_offset
        mbw = settings.map_box_width
        mbh = settings.map_box_height
        m = state.current_map
        for x in range(-size, size+1):
            for y in range(-size, size+1):
                e = event @ (x, y, xo, yo, mbw, mbh)
                for z in range(7, -1, -1):
                    cell = *e.grid, z
                    if cell not in visited:
                        if m[cell]:
                            tile = m[e.grid_x, e.grid_y, z][-1][0]
                            events.append((e,tile))
                        visited.append(cell)
        if events:
            executor = StackItem(map_del, event=events)
            executor.exec(self, stack=state.redo_stack)
            state.stack.append(executor)
              
    def draw(self, event, tile, clear_redo=True):
        tile_size = settings.tile_size
        size = state.tool_size - 1
        events = []
        current_map = state.current_map
        z = tile.layer
        for x in range(-size, size+1):
            for y in range(-size, size+1):
                e = event + (x, y)
                for item in current_map[(*e.grid, z)]:
                    if tile in item:
                        break
                else:
                    events.append(e)
        if events:
            executor = MapAdd((*events,), tile)
            executor.exec(self, stack=state.redo_stack)
            state.stack.append(executor)
                
    def old_draw(self, event, tile, clear_redo=True):
        
        gx, gy = event.grid
        for item in state.current_map[gx, gy, tile.layer]:
            if tile in item:
                return self.sentinel
            
        self.parent.has_been_modified = True
        executor = StackItem(map_add, event=event, tile=tile)
        executor.exec(self, stack=state.redo_stack)
        state.stack.append(executor)

        
    def old_erase(self, event):
        gx, gy = event.grid
        for z in range(7, -1, -1):
            if state.current_map[gx, gy, z]:
                tile, tag = state.current_map[gx, gy, z][-1]
                executor=StackItem(map_del, event=event, tile=tile)
                executor.exec(self, stack=state.redo_stack)
                state.stack.append(executor)
                self.parent.has_been_modified = True
                return
            
    def clear_canvas(self):
        map_ = state.current_map
        cdel = self.canvas.delete
        for k in map_:
            for tile, tag in map_[k]:
                cdel(tag)
                
    def redraw(self, *args):
        self.clear_canvas()
        state.build_map()
        for item in state.stack:
            item.exec(self)
                
class EditMapProperties:
    def __init__(self, parent):
        self.confirmed = False
        self.root = Toplevel(parent)
        self.root.title('Resize map')
        wvar = StringVar(value=settings.get_default('map_tile_width'))
        hvar = StringVar(value=settings.get_default('map_tile_height'))
        spinopts = dict(to=255, increment=2, width=12)
        propbox = LabelFrame(self.root, text='Map size')
        buttbox = Frame(self.root)
        map_width         = Label(propbox, text='Width', width=12)
        map_height        = Label(propbox, text='Height', width=12)
        width_spinner     = Spinbox(propbox,textvariable=wvar, **spinopts)
        height_spinner    = Spinbox(propbox, textvariable=hvar, **spinopts)
        ok                = Button(buttbox, text='Ok', width=10,
                                   command=self.confirm)
        cancel            = Button(buttbox, text='Cancel', width=10,
                                   command=self.cancel)
        propbox       .grid(row=0, column=0, sticky='n')
        buttbox       .grid(row=1,column=0)
        map_width     .grid(row=0, column=0)
        map_height    .grid(row=1, column=0)
        width_spinner .grid(row=0, column=1)
        height_spinner.grid(row=1, column=1)
        ok            .grid(row=0, column=0)
        cancel        .grid(row=0, column=1)
        wvar.set(value=str(settings.map_tile_width))
        hvar.set(value=str(settings.map_tile_height))
        self.wvar, self.hvar = wvar, hvar
        self.root.resizable(height=0, width=0)
        self.root.transient(parent) #???????
        self.root.grab_set()
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.wm_deiconify
        self.root.wait_window()

    def cancel(self, *args):
        pass

    def confirm(self, *args):
        width = int(self.wvar.get())
        height = int(self.hvar.get())
        if not 0 < width < 256:
            return messagebox.showerror(
                'Invalid map size', msg.format(k='width', v=width))
        if not 0 < height < 256:
            return messagebox.showerror(
                'Inavlid map size', msg.format(k='height', v=height))
        state.resize_map(width, height)
        settings.map_tile_width = width
        settings.map_tile_height = height
        self.confirmed = True
        self.destroy()
        
    def destroy(self, *args):
        self.root.destroy()

class MapPreview:
    def __init__(self, parent):
        self.root = Toplevel(parent)
        canvas = Canvas(self.root,
                        width=settings.map_width,
                        height=settings.map_height,
                        bg='#ec1ce0')
        canvas.grid(row=0, column=0)
        if settings.map_width > 1300:
            hbar = Scrollbar(self.root, orient='horizontal',
                             command=canvas.xview)
            hbar.grid(row=1, column=0, sticky='ew')
        if settings.map_height > 700:
            vbar = Scrollbar(self.root, orient='vertical',
                             command=canvas.yview)
            vbar.grid(row=0, column=1, sticky='ns')
        self.image = state.current_map.render()
        self.photo = PhotoImage(self.image)
        canvas.create_image(settings.map_width//2,settings.map_height//2,
                            image=self.photo)
        self.root.title('Previwing map')
        self.root.grab_set()
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.wm_deiconify
        self.root.wait_window()
        
class NewMapDialog:
    def __init__(self, parent):
        self.confirmed = False
        self.state = State()
        print(self.state.tiles==state.tiles, 'self.state.tiles==state.tiles')
        self.root = Toplevel(parent)
        self.root.title('Create new map')
        wvar = StringVar(value=settings.get_default('map_tile_width'))
        hvar = StringVar(value=settings.get_default('map_tile_height'))
        tile_size_var=StringVar()
        spinopts = dict(to=255, increment=2, width=12)
        okopts = dict(text='Ok', command=self.confirm, width=10)
        cancelopts=dict(text='Cancel', command=self.cancel, width=10)
        opentilesopts=dict(text='Load tile set from directory...',
                           command=self.open_tile_set_dir)
        propbox = LabelFrame(self.root, text='Map properties')
        tilebox = LabelFrame(self.root, text='Tile set preview')
        buttbox = Frame(self.root)
        lbuttbox = Frame(self.root)
        rbuttbox = Frame(self.root)
        self.canvas       = Canvas(tilebox, width=256, height=256)
        ok                = Button(lbuttbox, **okopts)
        cancel            = Button(lbuttbox, **cancelopts)
        opentilesetdir    = Button(rbuttbox, **opentilesopts)
        opentileset       = Button(rbuttbox, text='Open tile set',
                                   command=self.open_tile_set)
        map_width         = Label(propbox, text='Width', width=12)
        map_height        = Label(propbox, text='Height', width=12)
        tile_size         = Label(propbox, text='Tile size', width=12)
        width_spinner     = Spinbox(propbox,textvariable=wvar, **spinopts)
        height_spinner    = Spinbox(propbox, textvariable=hvar, **spinopts)        
        tile_size_spinner = Spinbox(propbox, textvariable=tile_size_var,
                                  values=(8,16,24,32,48,64),
                                  width=12)
        propbox          .grid(row=0, column=0, sticky='n')
        tilebox          .grid(row=0, column=1)
        lbuttbox         .grid(row=1, column=0)
        rbuttbox         .grid(row=1, column=1)
        map_width        .grid(row=0, column=0)
        map_height       .grid(row=1, column=0)
        tile_size        .grid(row=2, column=0)
        width_spinner    .grid(row=0, column=1)
        height_spinner   .grid(row=1, column=1)
        tile_size_spinner.grid(row=2, column=1)
        ok               .grid(row=0, column=0)
        cancel           .grid(row=0, column=1)
        opentilesetdir   .grid(row=0, column=0)
        opentileset      .grid(row=0, column=1)
        self.canvas      .grid()
        tile_size_var.set(value=settings.get_default('tile_size'))
        self.wvar, self.hvar, self.tile_size_var = wvar, hvar, tile_size_var
        self.root.resizable(height=0, width=0)
        self.root.transient(parent) #???????
        self.root.grab_set()
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.wm_deiconify
        self.root.wait_window()

    def _validate_tiles(self):
        size = (int(self.tile_size_var.get()),) * 2
        for tile in self.state.tiles.itertiles():
            if tile.image.size != size:
                return messagebox.showerror('Invalid tile size setting',
                    'Given tile size does not match loaded tile set')
        if size[0] % 8:
            return messagebox.showerror('Invalid tile size setting',
                                 'Given tile size is not a multiple of 8')

    def _open_tile_set(self):
        if self._validate_tiles() != None:
            return
        self.state.tiles.load_photos()
        photos['tile_set_preview'] = self.state.tiles.image
        self.canvas.create_image(128, 128, image=photos['tile_set_preview'])
        
    def open_tile_set(self, *args):
        filename = askopenfilename(parent=self.root,
                                   title='Open',
                                   filetypes=(('Tile set files', '*.til'),))
        if filename:
            with open(filename, 'rb') as file:
                self.state.tiles = pickle.load(file)
            self._open_tile_set()
            
        
    def open_tile_set_dir(self, *args):
        directory = askdirectory(parent=self.root,
                                   title='Open')
        if directory:            
            self.state.tiles = TileSet.from_directory(directory)
            self._open_tile_set()
            
    def confirm(self, *args):
        self._validate_tiles()
        width = int(self.wvar.get())
        height= int(self.hvar.get())
        msg = 'Invalid map {k}: {v!r}'
        if not 0 < width < 256:
            return messagebox.showerror(
                'Invalid map size', msg.format(k='width', v=width))
        if not 0 < height < 256:
            return messagebox.showerror(
                'Inavlid map size', msg.format(k='height', v=height))
                                                                       
        settings.map_tile_width = width
        settings.map_tile_height = height
        self.state.resize_map(width, height)
        self.confirmed = True
        self.destroy()
        
    def cancel(self, *args):
        pass
    
    def destroy(self, *args):
        self.root.destroy()

