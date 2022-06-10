from components.window import Window, WindowType
from components.animator import Animator
from components.looper import Looper
from threading import Thread

from modules.bar_workspaces import Main as WorkspacesMain
from modules.bar_stats import Main as StatsMain

from gi.repository import Gtk

from i3ipc import Connection

class Main(Looper):
    def __init__(self):
        super().__init__()
        
        self.bar = Window(WindowType.Bar)
        self.bar.create_window()

        self.i3_connection = Connection()
        
        self.main_animator = Animator(self.bar)
        self.main_animator.main_draw_callback = self.draw
        
        self.bar.connect_animated_overlay(self.main_animator)
        # self.bar.add(self.main_animator)
        
        self.bar.show_overlay()
        self.workspaces = WorkspacesMain(self.i3_connection)
        self.stats = StatsMain(self.bar)
        self.i3_t = Thread(target=self.i3_connection.main)
        self.i3_t.daemon = True
        self.i3_t.start()

        self.loop_init()

    def draw(self, context, width, height):
        self.workspaces.draw(context, height)
        self.stats.draw(context, width, height)

    def update(self, dt):
        self.workspaces.update(dt)
        self.stats.update(dt)
        self.main_animator.draw()
