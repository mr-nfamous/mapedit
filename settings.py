import os
from io import StringIO
from configparser import ConfigParser

DEFAULT_PATH = os.path.join(os.path.split(__file__)[0], r'resources\config.ini')
DEFAULT_CONFIG = '''
[defaults]
tile_size = 16
map_tile_width = 40
map_tile_height = 40
map_box_frame_size = 400
tile_set_dir = sets

[menu-keybindings]
new_map = <Control-n>
open_map = <Control-o>
save_map = <Control-s>
save_map_as = <Control-Shift-S>
save_tile_set_as = <Control-Shift-T>
undo = <Control-z>
redo = <Control-y>
add_remove_tiles = <Control-q>
edit_map_properties = <Control-p>

[file-open_map]
accelerator = Ctrl+ O
label = Open map

[file-new_map]
accelerator = Ctrl+ N
label = New map

[file-save_map]
accelerator = Ctrl+ S
label = Save map

[file-save_map_as]
accelerator = Ctrl+ Shift+ S
label = Save map as...

[file-save_tile_set_as]
accelerator = Ctrl+ Shift+ T
label = Save tile set as...

[edit-undo]
accelerator = Ctrl+ Z
label = Undo

[edit-redo]
accelerator = Ctrl+ Y
label = Redo

[edit-add_remove_tiles]
accelerator = Ctrl+ Q
label = Add/remove tiles

[edit-edit_map_properties]
accelerator = Ctrl+ P
label = Edit map properties

[edit-raise_all_layers]
label = Raise all layers

[edit-lower_all_layers]
label = Lower all layers

[edit-insert_row_top]
label = Insert row above

[edit-insert_column_left]
label = Insert column left

[view-preview]
label = Preview map
'''
def save(config, filename=DEFAULT_PATH):
    with open(filename, 'w') as file:
        config.write(file)
def load_config():
    config = ConfigParser()
    _config = ConfigParser()
    _config.read_file(StringIO(DEFAULT_CONFIG))    
    try:
        error = False
        with open(DEFAULT_PATH) as file:
            config.read_file(file)
    except:
        print("couldn't find config file. Creating a new one from defaults.")
        error = True
        config = _config
    else:                
        for section in _config.sections():
            try:
                a = set(config[section])
                b = set(_config[section])
                c = set(config[section]) ^ set(_config[section])
                assert not c
            except KeyError as e:
                error = True
                print(f'missing section in config file: {section}')
                config[section] = _config[section]
            except AssertionError:
                ops = ', '.join(c)
                print(f'config file contains unknown options {ops}')                    
            for option in _config[section].keys():
                try:
                    config[section][option]
                except KeyError as e:
                    error = True
                    error = f'missing option {option!r} in config[{section}]'
                    config[section][option] = _config[section][option]    
    if error:        
        save(config)
    return config

def load_settings():
    config = load_config()
    _defaults = ConfigParser() 
    with StringIO(DEFAULT_CONFIG) as file:        
        _defaults.read_file(file)
    _tile_size = config['defaults'].getint('tile_size')
    _map_box_frame_size = config['defaults'].getint('map_box_frame_size')
    _map_tile_width = config['defaults'].getint('map_tile_width')
    _map_tile_height = config['defaults'].getint('map_tile_height')
    _key_bindings = dict(config['menu-keybindings'])
    current_map_file = ''
    def menu_setting(d):
        def _property(key):
            def getter(self):
                return d[key]
            def setter(self):
                d[key] = value
            return property(getter, setter)
        
        class MenuSetting:
            def keys(self):
                return d.keys()
            def values(self):
                return d.values()
            def items(self):
                return d.items()
            def __iter__(self):
                return iter(d)
            def __len__(self):
                return len(d)
            def __getitem__(self, key):
                return d[key]
            def __repr__(self):
                return f'{type(self).__name__}({self.items()})'
        for k, v in d.items():
            setattr(MenuSetting, k, _property(k))
        return MenuSetting()
        
    class Settings:
        @classmethod
        def get_default(cls, key):
            return _defaults['defaults'][key]
        def save(self, filename=DEFAULT_PATH):
            with open(filename, 'w') as file:
                config.write(file)

        @property
        def key_bindings(self):
            return _key_bindings
        @property
        def filemenu(self):
            r = {}
            for key in _defaults:
                menu, sep, command = key.partition('-')
                if menu == 'file':
                    r[command] = {**_defaults[key]}
            return menu_setting(r)
        
        @property
        def editmenu(self):
            r = {}
            for key in _defaults:
                menu, sep, command = key.partition('-')
                if menu == 'edit':
                    r[command] = {**_defaults[key]}
            return menu_setting(r)

        @property
        def viewmenu(self):
            r = {}
            for key in _defaults:
                menu, sep, command = key.partition('-')
                if menu == 'view':
                    r[command] = {**_defaults[key]}
            return menu_setting(r)
        
        @property
        def tile_size(self):
            return _tile_size
        @tile_size.setter
        def tile_size(self, value):
            nonlocal _tile_size
            _tile_size = value
            config['defaults']['tile_size'] = str(value)
            
        @property
        def map_box_frame_size(self):
            return _map_box_frame_size
        @map_box_frame_size.setter
        def map_box_frame_size(self, value):
            nonlocal _map_box_frame_size
            _map_box_frame_size = value
            config['defaults']['map_box_frame_size'] = str(value)
            
        @property
        def map_tile_width(self):
            return _map_tile_width
        @map_tile_width.setter
        def map_tile_width(self, value):
            nonlocal _map_tile_width
            _map_tile_width = value
            config['defaults']['map_tile_width'] = str(value)
            
        @property
        def map_tile_height(self):
            return _map_tile_height
        @map_tile_height.setter
        def map_tile_height(self, value):
            nonlocal _map_tile_height
            _map_tile_height = value
            config['defaults']['map_tile_height']=str(value)

        @property
        def tile_image_size(self):
            return _tile_size, _tile_size
            
        @property
        def map_box_max_tiles(self):
            return (_map_box_frame_size - 16) // _tile_size
        
        @property
        def map_box_max_size(self):
            return _map_box_frame_size - 16
        
        @property
        def map_box_width(self):
            return min(_map_box_frame_size - 16, _map_tile_width * _tile_size)

        @property
        def map_box_height(self):
            return min(_map_box_frame_size-16, _map_tile_width *_tile_size)
        
        @property
        def map_box_tile_width(self):
            return min((_map_box_frame_size - 16)//_tile_size, _map_tile_width)
        
        @property
        def map_box_tile_height(self):
            return min((_map_box_frame_size-16)//_tile_size, _map_tile_height)
        
        @property
        def map_box_max_xscroll(self):
            return max(0, _map_tile_width - self.map_box_max_tiles)
        
        @property
        def map_box_max_yscroll(self):
            return max(0, _map_tile_height - self.map_box_max_tiles)
        
        @property
        def map_box_size(self):
            return self.map_box_width, self.map_box_height
        
        @property
        def map_box_tile_size(self):
            return self.map_box_tile_width, self.map_box_tile_height
        
        @property
        def map_width(self):
            return _map_tile_width * _tile_size
        
        @property
        def map_height(self):
            return _map_tile_height  * _tile_size
        
        @property
        def map_size(self):
            return self.map_width, self.map_height
        
        @property
        def map_tile_size(self):
            return _map_tile_width, _map_tile_height
            
        def __repr__(self):
            excl = ['filemenu', 'editmenu', 'viewmenu']
            lines = []
            for attr in excl:
                for k, v in getattr(self, attr).items():
                    for subk, subv in v.items():
                        lines.append(f'    {attr}.{k}[{subk!r}]={subv!r}')
            membs = filter(lambda x: x not in excl, self._members)
            lines.extend(
                f'    {attr}={getattr(self, attr)!r}' for attr in membs)
            values = '\n'.join(lines)
            return f'<settings>:\n{values}'
        
        def __getitem__(self, key):
            try:
                return getattr(self, key)
            except AttributeError:
                raise KeyError(key) from None
    members = [k for k, v in Settings.__dict__.items()
               if isinstance(v, property)]
    r = {}
    for key in _defaults:
        menu, sep, command = key.partition('-')
        if menu in ('file', 'edit'):
            r[command] = {**_defaults[key]}
    Settings._menuitems = r
    Settings._members = members
    return Settings()

class State:
    pass
state=State()
settings=load_settings()
