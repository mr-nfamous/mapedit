
import pprint
from mapedit import *
from mapedit.widgets import *
from mapedit.menu import MenuBar, register
from mapedit.map import *
from mapedit.palette import *
from stexit3 import execute as e

class App:
    never_disable = ('open_map', 'new_map')
    map_file = ''
    tile_set_file = ''
    tile_set_dir = ''
    def __init__(self):
        self.root = Tk()
        self._has_been_modified = False
        self.menu    = MenuBar(self)
        self.map     = MapBox(self)
        self.palette = Palette(self)
        self.map     .grid(column=0, row=0, sticky='nw')
        self.palette .grid(column=1, row=0, sticky='ne')
        self.map_file='aftereventrefactor.map'
        self._open_map()
        self.root.resizable(height=0, width=0)
        self.root.title('Map editor')
        self.root.mainloop()

    def enable(self):
        state.tiles.load_photos()
        state.build_map()
        state.current_tile = state.tiles[0,0]
        photos.selected_tile_image = state.current_tile.image.resize((48,48))
        self.palette.current_tile_label.config(image=photos.selected_tile_image)
        self.palette.canvas            .grid(row=0, column=0, columnspan=3)
        self.palette.sep1              .grid(row=1, column=0, columnspan=3,sticky='nsew',
                                             pady=5, padx=5)
        self.palette.tool_size_label.grid(row=2, column=0, sticky='nsew')
        self.palette.current_tile_label.grid(row=2, column=1, sticky='w',rowspan=2)
        self.palette.lbox.grid(row=3, column=0,sticky='nsew', padx=5)
        self.palette.sep2               .grid(row=4, column=0, sticky='nsew',
                                              columnspan=3, pady=5, padx=5)
        self.palette.layer_box         .grid(row=5, column=0, columnspan=3)
        
        self.map.unloaded.grid_forget()
        self.map.canvas.grid(row=0, column=0)
        self.map.clear_canvas()
        if settings.map_width > 400:
            self.map.canvas.config(width=384,
                                   xscrollincrement=settings.tile_size,
                                   xscrollcommand=self.map.hbar.set,)
            self.map.hbar.grid(row=1, column=0, sticky='ew')            
        else:
            self.map.vbar.grid_forget()
        if settings.map_height > 400:
            self.map.canvas.config(height=384,
                                   yscrollincrement=settings.tile_size,
                                   yscrollcommand=self.map.vbar.set,)
            self.map.vbar.grid(row=0, column=1, sticky='ns')            
        else:
            self.map.vbar.grid_forget()
        self.map.move_to_left()
        self.map.move_to_top()
        self.map.canvas.config(scrollregion=(0, 0, *settings.map_size))
        self.map.make_background()
        self.map.map_background = self.map.canvas.create_image(
            settings.map_width//2,
            settings.map_height//2,
            image=photos.map_background)

        for item in state.stack:
            item.exec(self.map)
        self.palette.update_layer_views()
        self.palette.refresh_photo()
        self.bind_events()
        self.menu.enable_all()

    def set_title(self):
        asterick = '*' if self.has_been_modified else ''
        size = f'{settings.map_tile_width}x{settings.map_tile_height}'
        msg = f'{asterick}{self.map_file} {size}{asterick}'
        self.root.title(f'Map Editor - {msg}')
        
    @property
    def has_been_modified(self):
        return self._has_been_modified
    @has_been_modified.setter
    def has_been_modified(self, value):
        self._has_been_modified = value
        self.set_title()
        
    @register('file', never_disable=True)
    def new_map(self, *args):
        newmapwin = NewMapDialog(self.root)
        if newmapwin.confirmed:
            state.update(newmapwin.state)
            self.enable()
            self.map_file = 'New map'
            
    @register('file', never_disable=True)
    def open_map(self, *args):
        filename= askopenfilename(parent=self.root,
                                   title='Open',
                                   filetypes=(('Map files', '.*map'),),
                                   initialfile=self.map_file)
        if filename:
            self.map_file = filename
            self._open_map()
    def _open_map(self):
        with open(self.map_file, 'rb') as file:
            s = pickle.load(file)
        self.has_been_modified = False
        state.update(s)
        self.enable()
        w = settings.map_tile_width
        h = settings.map_tile_height

    register.separator('file')

    def _save_map(self):
        data = pickle.dumps(state)
        with open(self.map_file, 'wb') as file:
            file.write(data)
            self.has_been_modified = False
    @register('file')
    def save_map(self, *args):
        if not self.map_file:
            self.save_map_as()
        self._save_map()
        
    @register('file')
    def save_map_as(self, *args):
        filename = asksaveasfilename(parent=self.root,
                                          title='Save as',
                                          filetypes=(('Map files', '.*map'),),
                                          initialfile=self.map_file,
                                          defaultextension='.map')
        if filename:
            self.map_file = filename
            self._save_map()
            self.root.title(f'Map editor - {self.map_file}')

    register.separator('file')

    @register('file')
    def save_tile_set_as(self, *args):
        filename = asksaveasfilename(parent=self.root,
                                     title='Save tile set as',
                                     filetypes=(('Tile set files', '.*til'),),
                                     initialfile='',
                                     defaultextension='.til')
        if filename:
            with open(filename, 'wb') as file:
                pickle.dump(state.tiles, file)
                
    @register('edit')
    def undo(self, *args):
        if not state.stack:
            return
        executor = state.stack.pop()
        if isinstance(executor, MapAdd):
            events, tile = executor.events, executor.tile
            for event in events:
                cell = state.current_map[(*event.grid, tile.layer)]
                tile, tag = cell.pop()
                self.map.canvas.delete(tag)
        elif isinstance(executor, MapDel):
            events = executor.events
            for event, tile in events:
                MapAdd((event,),tile).exec(self.map)
        state.redo_stack.append(executor)
        
    @property
    def cm(self):
        return state.current_map
    
    def old_undo(self, *args):
        if not state.stack:
            return
        executor = state.stack.pop()
        if executor.func is map_del:
            index = state.stack.index(StackItem(map_add, *executor.args))
            state.stack[index].exec(self.map)
        elif executor.func is map_add:
            event, tile = executor.args
            cell = state.current_map[(*event.grid, tile.layer)]
            tile, tag = cell.pop()
            self.map.canvas.delete(tag)
        state.redo_stack.append(executor)

    @register('edit')        
    def redo(self, *args):
        if not state.redo_stack:
            return
        executor = state.redo_stack.pop()
        executor.exec(self.map)
        state.stack.append(executor)

    register.separator('edit')

    @register('edit')
    def add_remove_tiles(self, *args):
        self.paletteeditorwin = PaletteEditor(self.root)
        if self.paletteeditorwin.status:
            state.tiles = self.paletteeditorwin.oldtiles
            state.tiles.load_photos()
        self.palette.refresh_photo()


    @register('edit')
    def edit_map_properties(self, *args):
        self.mapeditwin= EditMapProperties(self.root)
        if self.mapeditwin.confirmed:
            self.enable()
        
    register.separator('edit')
    @register('edit')
    def raise_all_layers(self, *args):
        for x,y in itergrid(16, 16):
            tile = state.tiles[x,y]
            tile.layer = min(tile.layer+1, 7)        
        self.palette.layer_select_buttons[state.current_tile.layer].select()
        self.palette.update_layer_views()

    @register('edit')
    def lower_all_layers(self, *args):
        for x, y in itergrid(16, 16):
            tile = state.tiles[x,y]
            tile.layer = max(0, tile.layer-1)
        self.palette.layer_select_buttons[state.current_tile.layer].select()
        self.palette.update_layer_views()

    register.separator('edit')
    @register('edit')
    def insert_row_top(self):
        settings.map_tile_height += 1
        state.map_y_offset += 1
        self.map.canvas.config(scrollregion=(0, 0, *settings.map_size))
        for i, executor in enumerate(state.stack):
            events = []
            if isinstance(executor, MapDel):
                for event, tile in executor.events:                    
                    events.append((event + (0, 1), tile))
            else:
                for event in executor.events:                
                    events.append(event + (0, 1))
            state.stack[i].events = tuple(events)
        for i, executor in enumerate(state.redo_stack):
            events = []
            if isinstance(executor, MapDel):
                for event, tile in executor.events:                    
                    events.append((event + (0, 1), tile))
            else:
                for event in executor.events:                
                    events.append(event + (0, 1))
            state.redo_stack[i].events = tuple(events)
        self.map.clear_canvas()
        state.build_map()
        self.map.move_to_top()
        self.map.make_background()
        for executor in state.stack:
            executor.exec(self.map)

    @register('edit')
    def insert_column_left(self):
        settings.map_tile_width += 1
        state.map_x_offset += 1
        self.map.canvas.config(scrollregion=(0, 0, *settings.map_size))
        for i, executor in enumerate(state.stack):
            events = []
            if isinstance(executor, MapDel):
                for event, tile in executor.events:                    
                    events.append((event + (1, 0), tile))
            else:
                for event in executor.events:                
                    events.append(event + (1, 0))
            state.stack[i].events = tuple(events)
        for i, executor in enumerate(state.redo_stack):
            events = []
            if isinstance(executor, MapDel):
                for event, tile in executor.events:                    
                    events.append((event + (1, 0), tile))
            else:
                for event in executor.events:                
                    events.append(event + (1, 0))
            state.redo_stack[i].events = tuple(events)
        self.map.clear_canvas()
        state.build_map()
        self.map.move_to_left()
        self.map.make_background()
        for executor in state.stack:
            executor.exec(self.map)
            
    @register('view')
    def preview(self, *args):
        MapPreview(self.root)

        
    def bind_events(self):
        _map, _palette = self.map, self.palette
        _map.canvas.bind('<Button-1>', _map.clickleft)
        _map.canvas.bind('<Button-3>', _map.clickright)
        _map.canvas.bind('<ButtonRelease-1>', _map.release)
        _map.canvas.bind('<ButtonRelease-3>', _map.release)
        _map.canvas.bind('<Motion>', _map.motion)
        _palette.canvas.bind('<Button-1>', _palette.clickleft)
        _palette.canvas.bind('<Motion>', _palette.motion)
        _palette.canvas.bind('<ButtonRelease-1>', _palette.releaseleft)
        _palette.canvas.bind('<Button-3>', _palette.clickright)
        _palette.canvas.bind('<ButtonRelease-3>', self.palette.releaseright)
        for cmd, key in settings.key_bindings.items():
            command = getattr(self, cmd)
            if command.can_be_disabled:
                self.root.bind(key, command)

    def unbind_events(self):
        _map, _palette = self.map, self.palette
        _map.canvas.unbind('<Button-1>')
        _map.canvas.unbind('<ButtonRelease-1>')
        _map.canvas.unbind('<Motion>')
        _palette.canvas.bind('<Button-1>')
        _palette.canvas.bind('<Motion>')
        _palette.canvas.bind('<ButtonRelease-1>')
        _palette.canvas.bind('<Button-3>')
        _palette.canvas.bind('<ButtonRelease-3>')
        self.root.unbind('<Control-z>')
        self.root.unbind('<Control-y>')
a=App()
self = a.map
