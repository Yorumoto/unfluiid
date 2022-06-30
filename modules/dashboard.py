from time import perf_counter as get_time

from components.looper import Looper
from components.window import Window, WindowType
from components.animator import Animator

from modules.dashboard_modules.util import mouse_hovering 

# messy importing shit
from modules.dashboard_modules.sysinfo import SysInfoWidget
from modules.dashboard_modules.calendar import CalendarWidget
from modules.dashboard_modules.weather import WeatherWidget
from modules.dashboard_modules.visualizer import VisualizerWidget
from modules.dashboard_modules.select import SelectWidget

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

        self.widgets = [SysInfoWidget(), WeatherWidget(), CalendarWidget(), VisualizerWidget(), SelectWidget()]

        for i, widget in enumerate(self.widgets):
            widget.main_widget = self
            widget._at = 0
            widget.appearance_del_timer = i * 0.0625

        self.x = 0
        self.y = 0
        self.width = 1000
        self.height = 600
        self.padding = 10

        self._at = 0
        self.appearance_timer = 0

        self.can_draw_widgets = False
        
        self.mouse_pressed_time = 0 # mouse pressed time
        self.mouse_pressing = False # mouse pressed

        self.about_to_zoom_timer = 0 # 
        self.zoomed_widget = None
        self.layout = None

        self.before_final_quit_timer = 0.2
        self.quiting = False

        self.loop_init()

    def quit(self):
        if self.quiting:
            return

        self.quiting = True

    def on_key_press(self, _, event):
        if event.hardware_keycode == 9:
            if self.zoomed_widget:
                self.zoomed_widget = None
            else:
                self.quit()

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

            if self.zoomed_widget is not None:
                return True

            delay = get_time() - self.mouse_pressed_time

            for widget in self.widgets:
                if widget.holding and self.zoomed_widget is not widget:
                    self.zoomed_widget = widget

                widget.on_release()
                widget.on_click(delay)

        return True

    def draw(self, ctx, width, height):
        if self.layout is None:
            self.layout = PangoCairo.create_layout(ctx)

        # self
        self.x = (width * 0.5) - (self.width * 0.5)
        self.y = (height * 0.5) - (self.height * 0.5)
        
        dx = self.x - ((1 - self.appearance_timer) * 400)
        dy = self.y

        ctx.set_source_rgba(0.175, 0.15, 0.15, self.appearance_timer)
        common.context.rounded_rectangle(ctx, dx, dy, self.width, self.height, 30)
        ctx.fill()
        common.context.rounded_shadow(ctx, dx, dy, self.width, self.height, depth_by=10, color=(0.15, 0.15, 0.12), width_offset=10, height_offset=10, \
                global_alpha=self.appearance_timer)
        
        # widgets
        if self.can_draw_widgets:
            zooming_widget = None

            for widget in self.widgets:
                if widget.zoom_timer > 0:
                    zooming_widget = widget
                    continue
                widget.draw(ctx, self.layout)

            if zooming_widget is not None:
                zooming_widget.draw(ctx, self.layout)
        else:
            self.can_draw_widgets = True
        
    
    def update(self, dt):
        # update variables
        self._at = max(min(self._at + (dt * (-6 if self.quiting else 6)), 1), 0)
        self.appearance_timer = pytweening.easeOutQuad(self._at)

        self.global_alpha = pytweening.easeInOutQuad(1 - self._ga)

        # position widgets
        device_position = self.window.pointer_device.get_position()

        # lesson learned: balance positioning on update

        for widget in self.widgets:
            widget.x = self.x + ((widget.start_x + widget.padding) * (1 - widget.zoom_timer)) \
                    + (widget.origin_offset_x * (1 - widget.appearance_timer))
            widget.y = self.y + ((widget.start_y + widget.padding) * (1 - widget.zoom_timer)) \
                    + (widget.origin_offset_y * (1 - widget.appearance_timer))
            widget.width = (widget.start_width * (1 - widget.zoom_timer)) + (self.width * (widget.zoom_timer))
            widget.height = (widget.start_height * (1 - widget.zoom_timer)) + (self.height * (widget.zoom_timer))

            widget.colliding = mouse_hovering(device_position, widget.x, widget.y, widget.width, widget.height)
            
            widget._zt = max(min(widget._zt + dt * (-4 + (self.zoomed_widget is widget) * 8), 1), 0)
            
            if widget.appearance_del_timer <= 0:
                widget._at = max(min(widget._at + dt * (-4 if self.quiting else 4), 1), 0)
            else:
                widget.appearance_del_timer -= dt

            widget.appearance_timer = pytweening.easeOutQuad(widget._at)
             
            widget.zoom_timer = pytweening.easeOutQuad(widget._zt)

            widget.update(dt, self.global_alpha * (1 if (self.zoomed_widget is None or self.zoomed_widget is widget) else (1 - self.zoomed_widget.zoom_timer)))

        # update widgets
        self.main_animator.draw()
        
        if self._at <= 0 and self.quiting:
            if self.before_final_quit_timer <= 0:
                for widget in self.widgets:
                    widget.on_quit()

                Gtk.main_quit()
            else:
                self.before_final_quit_timer -= dt
            
