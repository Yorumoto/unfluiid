from components.window import Window, WindowType
from components.animator import Animator
from components.looper import Looper

from modules.bar_workspaces import Main as WorkspacesMain

from gi.repository import Gtk

from i3ipc import Connection

class Main(Looper):
    def __init__(self):
        super().__init__()
        
        self.bar = Window(WindowType.Bar)
        self.bar.create_window()

        self.i3_connection = Connection()
        
        self.main_animator = Animator(self.bar)
        self.main_draw = self.draw
        self.bar.connect_animated_overlay(self.main_animator)

        self.workspaces = WorkspacesMain(self.i3_connection)
        print(self.workspaces)

        self.loop_init()

    def draw(context, width, height):
        print(width)

    def update(self, dt):
        self.main_animator.draw()
