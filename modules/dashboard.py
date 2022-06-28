from time import perf_counter as get_time

from components.looper import Looper
from components.window import Window, WindowType
from components.animator import Animator

from modules.dashboard_modules.util import mouse_hovering 

# messy importing shit
from modules.dashboard_modules.sysinfo import SysInfoWidget
from modules.dashboard_modules.calendar import CalendarWidget

import common.context
import pytweening
from gi.repository import Gtk, PangoCairo

class Main(Looper):
    def __init__(self):
        self.window = Window(WindowType.FullScreen)

        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw

        self.window.connect_animated_overlay(self.main_animator)

        self.window.create_window()

        self.window.grab()
        self.window.connect('key_press_event', self.on_key_press)
        self.window.connect('button_press_event', self.on_press)
        self.window.connect('button_release_event', self.on_release)

        self.global_alpha = 1
        
        self._ga = 0
        self._ft = 0
        self.full_screen_timer = 0

        self.widgets = [SysInfoWidget(), ]
        CalendarWidget()

        self.x = 0
        self.y = 0
        self.width = 1000
        self.height = 600
        self.padding = 10

        self.can_draw_widgets = False
        
        self.mouse_pressed_time = 0 # mouse pressed time
        self.mouse_pressing = False # mouse pressed

        self.about_to_zoom_timer = 0 # 
        self.zoomed_widget = None
        self.layout = None

        self.loop_init()

    def on_key_press(self, _, event):
        if event.hardware_keycode == 9:
            Gtk.main_quit()
            return

    def on_press(self, _, event):
        if not self.mouse_pressing:
            self.mouse_pressing = True
            self.mouse_pressed_time = get_time()

            for widget in self.widgets:
                widget.on_press(self.mouse_pressed_time)
                

        return True
    
    def on_release(self, _, event):
        if self.mouse_pressing:
            self.mouse_pressing = False
            delay = get_time() - self.mouse_pressed_time

            for widget in self.widgets:
                widget.on_release()
                widget.on_click(delay)

        return True

    def draw(self, ctx, width, height):
        if self.layout is None:
            self.layout = PangoCairo.create_layout(ctx)

        # self
        self.x = (width * 0.5) - (self.width * 0.5)
        self.y = (height * 0.5) - (self.height * 0.5)

        ctx.set_source_rgba(0.15, 0.135, 0.135, 1)
        common.context.rounded_rectangle(ctx, self.x, self.y, self.width, self.height, 30)
        ctx.fill()
        
        # widgets
        if self.can_draw_widgets:
            for widget in self.widgets:
                widget.draw(ctx, self.layout)
        else:
            self.can_draw_widgets = True
        
    
    def update(self, dt):
        # update variables
        self.global_alpha = pytweening.easeInOutQuad(1 - self._ga)
        
        # update widgets
        self.main_animator.draw()

        # position widgets
        device_position = self.window.pointer_device.get_position()

        for widget in self.widgets:
            widget.x = self.x + self.padding + widget.start_x
            widget.y = self.y + self.padding + widget.start_y
            widget.colliding = mouse_hovering(device_position, widget.x, widget.y, widget.width, widget.height)
            widget.update(dt, self.global_alpha)

