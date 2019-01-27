
from mapedit import *
from mapedit.widgets import *
#from alert import alert

            
class Palette(Widget):
    def __init__(self, parent):
        super().__init__(parent, LabelFrame, text='Choose a tile')
        self.canvas = self.create_canvas(256, 256, bg='#ec1ce0')
        photos.blank_current_tile = Image.new('RGBA', (48, 48))
        photos.palette_gridlines = make_cell_highlight_box(16, 16)
        photos.blank_palette = Image.new('RGBA', (256, 256))
        photos.view_mask = Image.new('RGBA', (16, 16), (64, 50, 50, 170))
        self.cell_highlight = make_cell_highlight_box(1, 1)
        self.palette_photo = self.canvas.create_image(128, 128,
                                                image=photos.blank_palette)
        self.current_tile_label=Label(self.box,
                                      image=photos.blank_current_tile,
                                      relief='sunken')
        self.tool_size_label=Label(self.box,
                                   text='Tool size')
        self.tool_size_var = StringVar()
        self.sep1 = Separator(self.box, orient='horizontal')
        self.sep2 = Separator(self.box, orient='horizontal')
        lbox = Combobox(self.box, textvariable=self.tool_size_var,width=4,
                        values=('1','2','3','4','5','6','7','8'))
        lbox.bind('<<ComboboxSelected>>', self.edit_tool_size)
        #lbox['values'] = ('1','2','3','4','5','6','7','8')
        lbox.current(0)
        self.lbox = lbox
        self.view_masks = odict()
        self.gridlines = self.canvas.create_image(128, 128,
                                                  image=photos.palette_gridlines)
        self.layer_var = IntVar()
        self.layer_view_vars = [IntVar() for i in range(8)]
        self.layer_box = Frame(self.box)
        self.layer_view_buttons   =[Checkbutton(self.layer_box,
                                                text=f'{i}',
                                                onvalue=1,
                                                offvalue=0,
                                                variable=self.layer_view_vars[i],
                                                indicatoron=0,
                                                command=self.update_layer_views,
                                                width=2)
                                    for i in range(8)]
        self.layer_select_buttons=[Radiobutton(self.layer_box,
                                               text=f'{i}',
                                               value=i,
                                               command=self.update_layer,
                                               variable=self.layer_var,
                                               indicatoron=0,
                                               width=2)
                                   for i in range(8)]                                                
        layer_view_label = Label(self.layer_box,
                                 text=  'Viewing layers:',
                                 relief='sunken',
                                 anchor='w')
        layer_select_label = Label(self.layer_box,
                                   text='Select layer:',
                                   relief='sunken',
                                   anchor='w')
        layer_view_label.grid(row=0,column=0, sticky='nsew')
        for i, button in enumerate(self.layer_view_buttons, 1):
            button.grid(row=0, column=i)
            button.select()
        layer_select_label.grid(row=1, column=0, sticky='nsew')
        for i, button in enumerate(self.layer_select_buttons,1):
            button.grid(row=1, column=i,sticky='nsew')

    def edit_tool_size(self, *args):
        state.tool_size = int(self.tool_size_var.get())
    def update_layer_views(self, *args):
        for i in range(len(self.view_masks)):
            self.canvas.delete(self.view_masks.popitem()[1])
        views = [i.get() for i in self.layer_view_vars]
        for x in range(16):
            for y in range(16):
                tile = state.tiles[x,y]
                if tile:
                    if not views[state.tiles[x,y].layer]:
                        self.view_masks[x,y]=self.canvas.create_image(
                            x*16+8, y*16+8, image=photos.view_mask)
                        
    def update_layer(self, *args):
        if state.current_tile:
            state.current_tile.layer = self.layer_var.get()
            self.update_layer_views()
            self.parent.map.redraw()
            self.parent.has_been_modified = True
            
    def get_first_and_last_tiles(self, event):
        return state.tiles.get(self.starting_event.grid), state.tiles.get(event.grid)

    def clickleft(self, event):
        self.left_is_active=True
        self.starting_event = mouse_event(event)

    def clickright(self, event):
        event = mouse_event(event)
        if event.grid in state.tiles:
            self.right_is_active = True
            self.starting_event = event
            self.rotation = None
            self.last_event = event
            self.tiles_need_image_update = True
            
    def releaseleft(self, event):
        self.left_is_active =  False
        event = mouse_event(event)
        start_tile, end_tile = self.get_first_and_last_tiles(event)
        if hasattr(self, 'drag_tile'):
            self.canvas.delete(self.drag_tile)
            del self.drag_tile
        if start_tile == end_tile:
            self.select(event)
        else:
            if not self.parent.has_been_modified:
                self.parent.has_been_modified = True
            self.swap(event)
        self.refresh_photo()
        self.update_layer_views()

    def releaseright(self, event):
        self.right_is_active = False
        event = mouse_event(event)
        start_tile, end_tile = self.get_first_and_last_tiles(event)
        if self.rotation:
            self.rotation = None
            if hasattr(self, 'drag_group'):
                self.canvas.delete(self.drag_group)
                del self.drag_group
                if not self.parent.has_been_modified:
                    self.parent.has_been_modified = True
        self.refresh_photo()
        self.update_layer_views()
        
    def motion(self,event):
        if self.left_is_active:
            event = mouse_event(event)
            if not hasattr(self, 'drag_tile') and event.grid in state.tiles:
                self.get_tile_drag_icon()
                self.drag_tile = self.canvas.create_image(
                    event._event.x, event._event.y, image=photos['drag_tile'])
                self.last_drag_event = event
            elif event.grid in state.tiles:
                dx, dy = event.tkevent_delta(self.last_drag_event)
                self.last_drag_event = event
                self.canvas.move(self.drag_tile, dx, dy)
        elif self.right_is_active:
            self.rmotion(event)

    def rmotion(self, event):
        event = mouse_event(event)
        dx, dy = event.grid_delta(self.last_event)
        if self.rotation is None:
            self.rotation = 'horizontal' if dx else 'vertical' if dy else None
        if self.rotation == 'horizontal':
            if dx:
                self.rotate_horizontally(event, dx)
        elif self.rotation == 'vertical':
            if dy:
                self.rotate_vertically(event, dy)
        self.last_event = event

    def rotate_horizontally(self, event, dx):
        x = event.grid_x
        y = self.starting_event.grid_y
        state.tiles.rotate_row(y, -dx)
        self.last_keyset = state.tiles.get_row_keys(y)
        img = self.get_row_drag_icon()
        x_offset = len(self.last_keyset) * 16 // 2
        if hasattr(self, 'drag_group'):
            self.canvas.delete(self.drag_group)
        self.drag_group = self.canvas.create_image(x_offset, y*16+8, image=img)

    def rotate_vertically(self, event, dy):
        x = self.starting_event.grid_x
        y = event.grid_y
        state.tiles.rotate_col(x, -dy)
        self.last_keyset = state.tiles.get_column_keys(x)
        img = self.get_column_drag_icon()
        y_offset = len(self.last_keyset) * 16 // 2
        if hasattr(self, 'drag_group'):
            self.canvas.delete(self.drag_group)
        self.drag_group = self.canvas.create_image(x*16+8, y_offset, image=img)

    def get_column_drag_icon(self):
        if self.tiles_need_image_update:
            self.refresh_photo(*self.last_keyset)
        height = len(self.last_keyset) * 16
        image = Image.new('RGBA', (16, height))
        highlight = self.cell_highlight
        for y, key in zip(range(0, height, 16),self.last_keyset):
            image.paste(state.tiles[key].image, (0, y), state.tiles[key].image)
            image.paste(highlight, (0, y), highlight)
        photos['drag_group'] = image
        return photos['drag_group']

    def get_row_drag_icon(self):
        if self.tiles_need_image_update:
            self.refresh_photo(*self.last_keyset)
        width = len(self.last_keyset) * 16
        image = Image.new('RGBA', (width, 16))
        highlight = self.cell_highlight
        for x, key in zip(range(0, width, 16), self.last_keyset):
            image.paste(state.tiles[key].image, (x, 0), state.tiles[key].image)
            image.paste(highlight, (x, 0), highlight)
        photos['drag_group'] = image
        return photos['drag_group']

    def get_tile_drag_icon(self):
        gx, gy = self.starting_event.grid
        if (gx, gy) in state.tiles:
            self.refresh_photo((gx, gy))
            image = Image.new('RGBA', (16, 16))
            tile_image = state.tiles[gx, gy].image
            image.paste(tile_image, (0, 0), tile_image)
            hl = self.cell_highlight
            image.paste(hl, (0, 0), hl)
            photos['drag_tile'] = image
            return photos['drag_tile']

    def select(self, event):
        if state.tiles.get(event.grid):
            state.current_tile = tile = state.tiles[event.grid_x, event.grid_y]
            photos.selected_tile_image = tile.image.resize((48, 48))
            self.current_tile_label.configure(image=photos.selected_tile_image)
            self.layer_var.set(tile.layer)
            self.layer_select_buttons[tile.layer].select()
            
    def swap(self, event):
        sx, sy = self.starting_event.grid_x, self.starting_event.grid_y
        ex, ey = event.grid_x, event.grid_y
        start, end = (sx, sy), (ex, ey)
        if start != end and start in state.tiles and end in state.tiles:
            state.tiles[start], state.tiles[end] = state.tiles[end], state.tiles[start]
            self.refresh_photo()

    def refresh_photo(self, *excl):
        #alert(self)
        self.canvas.delete(self.palette_photo)
        state.tiles.image_update(*excl)
        photos['tile_set_photo'] = state.tiles.image
        self.palette_photo = (
            self.canvas.create_image(128, 128, image=photos.tile_set_photo))
        

    def disable(self, *args):
        self.canvas.unbind('<Button-1>')
        self.canvas.delete(self.palette_photo)
        self.current_tile_label.configure(image=photos.blank_current_tile)

class PaletteEditor(Widget):
    def __init__(self, parent):
        self.root = Toplevel(parent)
        super().__init__(self, Frame)
        self.left = Canvas(self.root, width=256, height=256,
                           bg='pink',
                           highlightthickness=0,
                           border=0)
        self.rite = Canvas(self.root, width=256, height=256,
                           bg='blue',
                           highlightthickness=0,
                           border=0)
        self.left.bind('<Button-1>', self.clickleft)
        self.left.bind('<Motion>', self.l_motion)
        self.left.bind('<ButtonRelease-1>', self.releaseleft)
        self.rite.bind('<Button-1>', self.clickrite)
        self.rite.bind('<Motion>', self.r_motion)
        self.rite.bind('<ButtonRelease-1>', self.releaserite)
        self.oldtiles = state.tiles.copy()
        self.refresh_photos(left=False)
        self.added_tiles = []
        self.open_set_button = Button(self.root, text='Open tile set...',
                                      command=self.open_tile_set)
        self.open_dir_button = Button(self.root, text='Load directory...',
                                      command=self.open_directory)
        self.left.grid(row=0, column=0, columnspan=2)
        self.rite.grid(row=0, column=2, columnspan=2)
        self.open_set_button.grid(row=1, column=0, sticky='ew')
        self.open_dir_button.grid(row=1, column=1, sticky='ew')
        self.lisactive = False
        self.risactive = False
        self.l_moved = False
        self.r_moved = False
        self.isloaded = False
        self.status = None
        self.root.title('Edit tile set')
        self.root.resizable(height=0, width=0)
        self.root.transient(parent) #???????
        self.root.grab_set()
        self.root.protocol("WM_DELETE_WINDOW", self.destroy)
        self.root.wm_deiconify
        self.root.wait_window()

    def open_directory(self, *args):
        self.dname = askdirectory(parent=self.root, title='Load directory')
        try:
            self.newtiles = TileSet.from_directory(self.dname)
        except PermissionError:
            messagebox.showerror('Invalid folder', f'{self.dname!r}')
            return
        current = [*self.oldtiles.itertiles()]
        dupes = filter(lambda tile: tile and tile in current,
                       [*self.newtiles.itertiles()])
        for dupe in dupes:
            self.newtiles.remove_tile(dupe)
        self.refresh_photos(rite=False)
        self.isloaded = True

    def open_tile_set(self, *args):
        self.dname = askopenfilename(filetypes=(('Tile sets', '*.til'),),
                                   title='Open Tile Set',
                                   parent=self.root)
        try:
            self.newtiles = TileSet.open(self.dname)
        except:
            messagebox.showerror('Invalid tile set file', f'{self.dname!r}')
            return
        if os.path.exists(self.dname):
            self.newtiles = TileSet.open(self.dname)
            self.refresh_photos(rite=False)
        self.isloaded = True

    def left_to_rite(self, event):
        tile = self.newtiles[event.grid]
        if tile:
            if not all(self.oldtiles.itertiles()):
                self.newtiles.remove_tile(tile)
                self.oldtiles.insert(tile)
                self.added_tiles.append(tile)
                self.refresh_photos()
            else:
                raise ValueError('current tile box is full')

    def clickleft(self, event):
        if self.isloaded:
            self.lisactive = True

    def releaseleft(self, event):
        if self.isloaded:
            self.lisactive = False
            if not self.l_moved:
                self.left_to_rite(mouse_event(event))
            self.l_moved = False

    def l_motion(self, event):
        if self.lisactive:
            event = mouse_event(event)
            self.left_to_rite(event)

    def clickrite(self, event):
        if self.isloaded:
            self.risactive = True

    def releaserite(self, event):
        if self.isloaded:
            self.risactive = False
            if not self.r_moved:
                self.rite_to_left(mouse_event(event))
            self.r_moved = False

    def r_motion(self, event):
        if self.risactive:
            event = mouse_event(event)
            self.rite_to_left(event)

    def rite_to_left(self, event):
        tile = self.oldtiles[event.grid]
        if tile in self.added_tiles:
            self.oldtiles.remove_tile(tile)
            self.newtiles.insert(tile)
            self.added_tiles.remove(tile)
            self.refresh_photos()

    def refresh_photos(self, left=True, rite=True):
        if left:
            photos['left_image'] = self.newtiles.image
            if hasattr(self, 'left_image'):
                self.left.delete(self.left_image)
            self.left_image = self.left.create_image(128, 128,
                                                     image=photos['left_image'])
        if rite:
            photos['rite_image'] = self.oldtiles.image
            if hasattr(self, 'rite_image'):
                self.rite.delete(self.rite_image)
            self.rite_image = self.rite.create_image(128, 128,
                                                     image=photos['rite_image'])
    def enable(self):
        pass

    def disable(self):
        pass

    def destroy(self):
        if self.added_tiles:
            self.status = messagebox.askyesnocancel('Keep Current Changes',
                        'Keep changes made to the current tile set?')
            if self.status is None:
                return
        self.root.destroy()

