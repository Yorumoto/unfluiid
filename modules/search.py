from components.looper import Looper
from components.window import Window, WindowType
from components.animator import Animator
from gi.repository import Gtk

import common.context
import pytweening

class Main(Looper):
    def __init__(self):
        super().__init__()

        self.window = Window(WindowType.FullScreen, transparent=True)
        self.force_grab = False

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

        ctx.translate((width * 0.5) - (600 * (1 - _at)), height * 0.5)
        ctx.set_source_rgba(0.8, 0.8, 0.8, self._at)
        common.context.rounded_shadow(ctx, -200, -200, 400, 400, radius=15, depth_alpha=0.125, depth_by=40, global_alpha=self._at)
        common.context.rounded_rectangle(ctx, -200, -200, 400, 400, 15)
        ctx.fill()

    def on_key_press(self, _, event):
        keycode = event.hardware_keycode
        string = event.string
        
        if keycode == 9:
            Gtk.main_quit()
            return True

        return True

    
