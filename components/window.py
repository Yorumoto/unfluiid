from gi.repository import Gtk, Gdk

import os
from enum import Enum

from time import sleep as wait
from Xlib import X
from Xlib.display import Display

display = Display()
gdk_display = Gdk.Display.get_default()

class WindowType(Enum):
    Bar = 0
    # Floating = 1
    FullScreen = 1

class Window(Gtk.Window):
    _bar_size = 45

    def __init__(self, window_type, transparent=True):
        super().__init__(decorated=False)
       
        self.screen = self.get_screen()
        
        if transparent:
            self.set_app_paintable(True)
            self.set_visual(self.screen.get_rgba_visual())

        self.overlay = Gtk.Overlay()

        self.widgets = Gtk.Box()

        self.overlay.add(self.widgets)
        self.animated_overlay = None

        self.monitor = None
        self.x11_toplevel = None
        self.toplevel = None
        self.force_grab = True

        self.add(self.overlay) 

        self.window_type = window_type
        self.connect('delete-event', Gtk.main_quit)
   
    def connect_animated_overlay(self, animated_overlay):
        self.animated_overlay = animated_overlay
        self.overlay.add_overlay(self.animated_overlay)

    def show_overlay(self):
        self.overlay.show_all()

    _grab_event_mask_pointer = Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.POINTER_MOTION_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK
    _grab_event_mask_keyboard = Gdk.EventMask.KEY_PRESS_MASK | Gdk.EventMask.KEY_RELEASE_MASK

    def _grab(self, no_pointer=False, no_keyboard=False):
        _current_time = Gdk.CURRENT_TIME
        _last_cursor = Gdk.Cursor(Gdk.CursorType.LAST_CURSOR)

        pointer_result = self.pointer_device.grab(self.toplevel, Gdk.GrabOwnership.NONE, False, self._grab_event_mask_pointer, _last_cursor, _current_time) \
                if not no_pointer else Gdk.GrabStatus.SUCCESS

        keyboard_result = self.keyboard_device.grab(self.toplevel, Gdk.GrabOwnership.NONE, False, self._grab_event_mask_keyboard, _last_cursor, _current_time) \
                if not no_keyboard else Gdk.GrabStatus.SUCCESS

        return pointer_result == Gdk.GrabStatus.SUCCESS and keyboard_result == Gdk.GrabStatus.SUCCESS

    def grab(self, **args): 
        if self.force_grab:
            while not self._grab(**args):
                    pass
        else:
            if not self._grab(**args):
                raise SystemExit("Failed to grab input, exiting...")

        self.x11_toplevel.map()

    def ungrab(self):
        pass

    def create_window(self):
        if self.window_type == WindowType.Bar:
            self.set_border_width(5)
            self.set_size_request(0, self._bar_size)
            self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        
        self.show_all()
        
        self.toplevel = self.get_toplevel().get_window()

        self.seat = gdk_display.get_default_seat()
        self.pointer_device = self.seat.get_pointer()
        self.keyboard_device = self.seat.get_keyboard() # forgot to change, and there we go, i did magic!

        self.x11_toplevel = display.create_resource_object('window', self.toplevel.get_xid())

        if self.window_type == WindowType.Bar:
            # reserve some space
            # https://gist.github.com/johnlane/351adff97df196add08a

            self.x11_toplevel.change_property(display.intern_atom('_NET_WM_STRUT'), display.intern_atom('CARDINAL'), 32, [0, 0, self._bar_size, 0], X.PropModeReplace)
            self.x11_toplevel.change_property(display.intern_atom('_NET_WM_STRUT_PARTIAL'), display.intern_atom('CARDINAL'), 32, [0, 0, self._bar_size, 0, 0, 0, 0, 0, 0, 0], X.PropModeReplace)
        elif self.window_type == WindowType.FullScreen:
            self.set_keep_above(True) 
            # override-redirect
            self.x11_toplevel.change_attributes(override_redirect=1)
            self.x11_toplevel.set_wm_protocols([display.intern_atom('WM_TAKE_FOCUS')])
            self.x11_toplevel.get_attributes()

            # if self.window_type == WindowType.FullScreen:
            monitor = self.screen.get_monitor_geometry(self.screen.get_monitor_at_window(self.toplevel)) # feels like c tho right?
            self.set_size_request(monitor.width, monitor.height)

            # focus the window
            self.x11_toplevel.map()

