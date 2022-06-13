from ctypes import POINTER
import os
import subprocess
from components.looper import Looper
from components.animator import Animator
from components.window import Window, WindowType

import cairo
import pytweening
import common.context

from gi.repository import Gtk
from enum import Enum

class ItemType(Enum):
    Shutdown = 1
    Restart = 2
    Suspend = 3
    Logout = 4

class Item:
    _item_icons = {
        ItemType.Shutdown: "",
        ItemType.Restart: "",
        ItemType.Suspend: "",
        ItemType.Logout: "",
    }

    _sub_item_icons = {
        True: "",
        False: ""
    }

    _small_size = (250, 300)
    _default_color = (0.2, 0.2, 0.2)
    _default_sub_color = (0.25, 0.25, 0.25)

    _selected_color = (242/255-0.2, 166/255-0.2, 150/255-0.2)
    _selected_sub_color = (242/255-0.3, 166/255-0.3, 150/255-0.3)

    def __init__(self, item_type, delay_time=0):
        self.item_type = item_type

        self.x = 0
        self.y = 0

        self.width = self._small_size[0]
        self.height = self._small_size[1]

        self._st = 0 # select time
        self._sat = 0 # select alternate time

        self._sht = [0, 0] # _sh(i)t : sub hover times

        self._ht = 0 # hover time
        self._at = 0 # appearance time
        self._att = delay_time # appearance delay time
        
        self.sub_item_select = 0

    def set_order(self, index, length):
        self.index = index
        self.length = length
        return self

    def update(self, dt, selected, one_selected, hovering, quitting):
        if self._att > 0:
            self._att -= dt
        else:
            self._at = max(min(self._at + dt * (-3 if quitting else 3), 1), 0)

            if self._at > 0.7:
                self._ht = max(min(self._ht + dt * (5 if hovering else -5), 1), 0)

        self._st = max(min(self._st + dt * (3 if selected else -3), 1), 0)
        self._sat = max(min(self._sat + dt * (3 if (not selected and one_selected) else -3), 1), 0)

        for i in range(2):
            self._sht[i] = max(min(self._sht[i] + dt * (3 if (selected and self.sub_item_select == i) else -3), 1), 0)


        # funny basic arithmetic magic
        
        _st = pytweening.easeInOutQuad(self._st)
        self.x = (((-((self.length * (self.width + 15)) * 0.5)) + (self.index * (self.width + 15))) * (1 - _st)) - (self.width * 0.5 * _st)
        self.y = (self.height * -0.5)

        self.width = self._small_size[0] + (_st * 600)
        self.height = self._small_size[1] + (_st * 150)

    def draw(self, ctx):
        _at = pytweening.easeOutQuad(self._at)
        _ht = pytweening.easeInOutQuad(self._ht)
        _st = pytweening.easeInOutQuad(self._st)
        _sat = pytweening.easeInOutQuad(self._sat)
        # _stt = min(_st * 2, 1)

        ctx.set_source_rgba(
                self._default_color[0] + self._selected_color[0] * _ht,
                self._default_color[1] + self._selected_color[1] * _ht,
                self._default_color[2] + self._selected_color[1] * _ht,
        _at * (1 - _sat))

        common.context.rounded_rectangle(ctx, self.x, self.y + ((1 - _at) * 200), self.width, self.height, self.height * 0.06125)
        ctx.fill()

        ctx.save()
        # ctx.move_to(self.width * 0.5, self.height * 0.5)
        ctx.translate((self.x + self.width * 0.5) - 35, (self.y + self.height * 0.5) + 35 + ((1 - _at) * 200))

        r = 1 - _ht
        ctx.set_source_rgba(r, r, r, _at * (1 - _st) * (1 - _sat))
        
        ctx.show_text(self._item_icons.get(self.item_type))
        ctx.restore()
        
        ctx.save()
        ctx.select_font_face("Iosevka Term", cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)
        ctx.set_font_size(100)

        ctx.translate(self.x + ((1 - _st) * (self.width * 2.6)), self.y + ((1 - _at) * 200))

        for i in range(2):
            w = self.width * 0.5 - 20
            h = self.height - 20
            x = 10 + (i * ((self.width * 0.5) - 5))
            
            _sht = pytweening.easeInOutQuad(self._sht[i])

            ctx.set_source_rgba(
                self._default_sub_color[0] + self._selected_sub_color[0] * _sht,
                self._default_sub_color[1] + self._selected_sub_color[1] * _sht,
                self._default_sub_color[2] + self._selected_sub_color[2] * _sht,
            _st)

            common.context.rounded_rectangle(ctx, x, 10, w, h, 25)
            ctx.fill()

            ctx.save()

            rr = 1 - _sht
            ctx.set_source_rgba(rr, rr, rr, _st)
            ctx.move_to(x + (w * 0.5 - 20), h * 0.5 + 50)
            ctx.show_text(self._sub_item_icons[i == 1])
            ctx.restore()

        ctx.restore()
 
class Main(Looper):
    commands = {
        ItemType.Shutdown: ['poweroff'],
        ItemType.Restart: ['reboot'],
        ItemType.Suspend: [os.path.join(os.path.dirname(__file__), "../", "main.py"), "screenflash"],
        ItemType.Logout: [], # are you in sway or i3?
    }

    def __init__(self):
        super().__init__()

        ##
        desktop_session = os.environ.get('DESKTOP_SESSION')

        if desktop_session in ['i3', 'sway']: # i'm not sure if sway has it
            self.commands[ItemType.Logout] = ['i3-msg', 'exit']

        ##

        self.execute_timer = 1
        self.no_input_timer = 10
        self.no_input = True

        self.items = [Item(x, 0.25 + (i * 0.125)).set_order(i, 4) for i, x in enumerate([ItemType.Shutdown, ItemType.Restart, ItemType.Suspend, ItemType.Logout])]

        self.window = Window(WindowType.FullScreen)

        self.command_type = None

        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw
        self.window.connect_animated_overlay(self.main_animator)

        self.window.connect('key_press_event', self.on_key_press)
        self.window.create_window()
        self.window.grab()


        self.hover_index = 0
        self.select_index = 0
        self.selecting = False
        self.quitted = False

        self.loop_init()

    def on_key_press(self, _, event):
        keycode = event.hardware_keycode
        string = event.string

        if keycode == 9:
            if self.selecting:
                self.items[self.select_index].sub_item_select = 0
                self.selecting = False
            else:
                self.quit()
                # Gtk.main_quit() # instead of exiting abruptly, how about i make a gradual exiting animation
            return True

        if self.items[0]._at > 0.8 and not self.quitted:
            self.no_input = False

            if keycode == 36:
                if self.selecting:
                    if self.items[self.select_index].sub_item_select == 0:
                        self.selecting = False
                    else:
                        self.command_type = self.items[self.select_index].item_type
                        self.quit(0.25)
                else:
                    self.select_index = self.hover_index
                    self.selecting = True
            elif keycode in [113, 114]:
                if self.selecting:
                    self.items[self.select_index].sub_item_select = (self.items[self.select_index].sub_item_select + (1 if keycode == 114 else -1)) % 2
                else:
                    self.hover_index = (self.hover_index + (1 if keycode == 114 else -1)) % len(self.items) 

        return True

    def draw(self, ctx, width, height):
        ctx.translate(width * 0.5, height * 0.5)
        ctx.set_font_size(70)
        ctx.select_font_face("feather", cairo.FontSlant.NORMAL, cairo.FontWeight.NORMAL)

        selected_items = []

        for index, item in enumerate(self.items):
            if item._st > 0.1:
                selected_items.append(item)
                continue

            item.draw(ctx)

        for item in selected_items:
            item.draw(ctx)

    def quit(self, delay=0):
        for i, item in enumerate(self.items):
            item._att = (i * 0.125) + delay

        self.quitted = True

    def run_command(self):
        try:
            command = self.commands[self.command_type]
            subprocess.Popen(['nohup'] + command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except KeyError:
            pass

    def update(self, dt):
        # size = self.window.get_size()

        for index, item in enumerate(self.items):
            item.update(
                dt, 
                index == self.select_index and self.selecting and not self.quitted, 
                self.selecting and not self.quitted,
                index == self.hover_index and not self.selecting and not self.quitted,
                self.quitted
            )

        if not self.quitted and self.no_input:
            if self.no_input_timer > 0:
                self.no_input_timer -= dt
            else:
                self.quit()

        if self.quitted and self.items[len(self.items) - 1]._at <= 0:
            if self.execute_timer > 0 and self.command_type in self.commands:
                self.execute_timer -= dt
            else:
                self.run_command()
                Gtk.main_quit()

        self.main_animator.draw()

        
