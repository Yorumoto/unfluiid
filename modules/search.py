from components.looper import Looper
from components.window import Window, WindowType
from components.animator import Animator
from gi.repository import Gtk

import common.context
import pytweening

class CurrentState: # struct :trollface:
    query = ""
    width = 600
    global_alpha = 0


class EntryContainer:
    def __init__(self, current_state):
        self.current_state = current_state

    def draw(self, ctx):
        ctx.set_source_rgba(1, 1, 1, self.current_state.global_alpha)
        common.context.rounded_rectangle(ctx, 0, -30, self.current_state.width, 60, 15)
        ctx.fill()

class Main(Looper):
    def __init__(self):
        super().__init__()

        self.current_state = CurrentState()

        self.window = Window(WindowType.FullScreen, transparent=True)
        self.force_grab = False
        
        self.container_test = EntryContainer(self.current_state)
        
        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw
        self.window.connect_animated_overlay(self.main_animator)

        self.window.create_window()
        self.window.connect('key_press_event', self.on_key_press)
        self.window.grab()

        self._at = 0 # appearance timer

        self.loop_init()


    def update(self, dt):
        self._at = min(self._at + dt * 2, 1)

        self.main_animator.draw()

    def draw(self, ctx, width, height):
        _at = pytweening.easeInOutQuad(self._at)
        self.current_state.global_alpha = _at

        ctx.translate((width * 0.5) - (600 * (1 - _at)) - (self.current_state.width * 0.5), height * 0.5)
        self.container_test.draw(ctx)

    def on_key_press(self, _, event):
        keycode = event.hardware_keycode
        string = event.string
        
        if keycode == 9:
            Gtk.main_quit()
            return True

        return True

    
