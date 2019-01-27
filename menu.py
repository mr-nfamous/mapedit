
from mapedit.widgets import *

_menu_registry = {}
_never_disable = []
class Sentinel:
    def __repr__(self):
        return f'<separator>'
SEPARATOR = Sentinel()

def register(menu, never_disable=False):
    def wrapper(method):
        _menu_registry[menu].append(method.__name__)
        if never_disable:
            _never_disable.append(method.__name__)
            method.can_be_disabled = False
        else:
            method.can_be_disabled = True
        return method
    if menu not in _menu_registry:
        _menu_registry[menu] = []
        
    return wrapper

def _register_separator(menu):
    _menu_registry[menu].append(SEPARATOR)

register.separator = _register_separator

class MenuBar(Menu):
    
    def __init__(self, parent):
        super().__init__(parent.root)
        self.parent = parent
        self.__keys = {menu:{cmd:i for i, cmd in enumerate(commands)
                             if cmd is not SEPARATOR}
                       for menu, commands in _menu_registry.items()}        
        for menu, commands in _menu_registry.items():
            setattr(self, menu, Menu(self, tearoff=0))
            self.add_cascade(label=menu.title(), menu=getattr(self, menu))
            for command in commands:
                _menu = getattr(self, menu)
                if command is SEPARATOR:
                    _menu.add_separator()
                else:
                    self.new_command(menu, command)
        parent.root.configure(menu=self)
        self.disable_all()
        
    def new_command(self, menu, cmd):
        getattr(self, menu).add_command(command=getattr(self.parent, cmd),
                                        **getattr(settings, f'{menu}menu')[cmd])

    def enable_command(self, menu, cmd):
        getattr(self, menu).entryconfig(self.__keys[menu][cmd],state='disabled')

    def disable_command(self, menu, cmd):
        getattr(self, menu).entryconfig(self.__keys[menu][cmd],state='normal')

    def disable_all(self):
        for menu, commands in self.__keys.items():
            for cmd, key in commands.items():
                if cmd not in _never_disable:
                    getattr(self, menu).entryconfig(key, state='disabled')

    def enable_all(self):
        for menu, commands in self.__keys.items():
            for cmd, key in commands.items():
                getattr(self, menu).entryconfig(key, state='normal')


