from components.looper import Looper
from components.window import Window, WindowType
from gi.repository import Gtk, Gdk
from components.animator import Animator

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from dbus import SystemBus

import time
import subprocess
import pytweening

class Main(Looper):
    def __init__(self):
        super().__init__()

        DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.bus.add_signal_receiver(self.handle_sleep, 'PrepareForSleep', 'org.freedesktop.login1.Manager', 'org.freedesktop.login1')

        self.window = Window(WindowType.FullScreen)
        self.window.create_window()
        self.window.toplevel.set_cursor(Gdk.Cursor(Gdk.CursorType.BLANK_CURSOR))

        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw
        self.window.connect_animated_overlay(self.main_animator)
        self.window.show_overlay()

        self._t = 0
        self.close = True
        self.sleep = False
        self.awake = False
        self.sleep_timer = 2.0

        self.loop_init()

    def handle_sleep(self, slept):
        if slept:
            return

        self.awake = True
       
    def draw(self, context, width, height):
        _t = pytweening.easeInOutExpo(self._t)
        
        context.set_source_rgba(1, 1, 1, _t)
        context.rectangle(0, 0, width, height)
        context.fill()
        
        frame_height = height * 0.5 * _t

        context.set_source_rgba(0, 0, 0, 1)
        context.rectangle(0, 0, width, frame_height)
        context.fill()
        
        context.rectangle(0, height - frame_height, width, frame_height)
        context.fill()

    def update(self, dt):
        if self._t >= 1 and not self.sleep:
            if self.sleep_timer <= 0:
                subprocess.run(['systemctl', 'suspend'])
                self.sleep_timer = 2.25 # it will disappear before linux connects it to my monitor
                self.sleep = True
            else:
                self.sleep_timer -= dt
        elif self.sleep and self.awake:
            if self.sleep_timer <= 0:
                self._t = max(self._t - (dt * 0.65), 0)

                if self._t <= 0:
                    Gtk.main_quit()
            else:
                self.sleep_timer -= dt
        else:
            self._t = min(self._t + (dt * 0.65), 1)

        self.main_animator.draw()
        
