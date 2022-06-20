from components.window import Window, WindowType
from components.textbox import Textbox
from components.animator import Animator
from components.looper import Looper
from components.tween import DeltaTween

from enum import Enum
from threading import Thread

from random import randint

import pytweening
import common.context
from gi.repository import Gtk, Pango, PangoCairo

import time
import os

INPUT_BAR_FONT = Pango.FontDescription("Iosevka Term 25")

class MenuType(Enum):
    Unknown = -1
    Shell = 0
    Dmenu = 1

class CurrentState:
    active_menu_type = MenuType.Unknown

    input_bar_height = 50
    layout = None
    
    entries = []
    entries_len = 0 # update
    total_entries_len = 0 # update pls
    
    entry_index = 0
    entry_page = 0

    cursor_transparency = 0
    loaded_transparency = 0

    searched = False
    searching = False
    loaded = False

    view_size = 15

    width = 800
    query : Textbox

    def update_page(self):
        self.entry_page = self.entry_index // self.view_size
        # print(self.entry_index, self.view_size, self.entry_page)

    def get_page_offset(self):
        return self.entry_page * self.view_size, (self.entry_page * self.view_size) + self.view_size

class EntryAction:
    pass

class Entry:
    name = ""
    actions = []
    short_description = ""
    description = ""
    icon = None

class EntryMenu:
    symbol = ""
    background = (0.22, 0.215, 0.22)

    def __init__(self, current_state):
        self.current_state = current_state

        self._sia = DeltaTween(target=0)
        self._rtt = 0 # results transparency timer
        
        self.entries = {} # [EntryObject] -> [EntryShiftTimer, EntryShiftDelayTimer, IsLeaving]

        self.last_page = None
        self.last_entries_len = None
        self.NOPE = False

    # i was today years old that i found out that python does 
    # the parent's method first before the child's method, wow...
    # (noticed when cursor blinking)
    
    def update(self, dt):
        entries_len = self.current_state.entries_len
        page = self.current_state.entry_page

        if entries_len != self.last_entries_len or page != self.last_page:
            start, end = self.current_state.get_page_offset()

            page_entries = self.current_state.entries[start:end]

            for index, (entry, value) in enumerate(self.entries.items()):
                value[2] = True

            for rel_index, entry in enumerate(page_entries):
                self.entries[entry] = [0, rel_index * (0.125 * 0.25), False]

            self._sia.change_target(entries_len)

        self._sia.update(dt * 4)
        self._rtt = max(min(self._rtt + (dt * (3 if entries_len else -3)), 1), 0)
        
        new_entries = {}

        for entry, timers in self.entries.items():
            if timers[1] > 0:
                timers[1] -= dt
                continue

            timers[0] = min(timers[0] + dt * 4, 1)
            
            print(timers, timers[2])
            if not timers[2]:
                print('yes', entry.name)
                new_entries[entry] = timers

        print(len(new_entries))
        self.entries = new_entries

        self.last_entries_len = entries_len
        self.last_page = self.current_state.entry_page

    def draw(self, ctx):
        pass

    def input_bar_draw(self, ctx, offset):
        ctx.save()
        ctx.translate(0, -offset)

        ctx.set_source_rgba(*self.background, 1)
        common.context.rounded_rectangle(ctx, 0, -self.current_state.input_bar_height * 0.5, self.current_state.width, self.current_state.input_bar_height, 20)
        ctx.fill()
        
        ctx.set_source_rgba(1, 1, 1, 1)

        (query_start, query_end), rel_cursor_position = self.current_state.query.get_bounds(44)
        query_text = self.current_state.query.input[query_start:query_end]
        text_bounds = common.context.text_bounds(self.current_state.layout, self.current_state.query.input[:rel_cursor_position])
         
        self.current_state.layout.set_font_description(INPUT_BAR_FONT)
        
        ctx.save()
        ctx.translate(45, -20)
        common.context.text(ctx, self.current_state.layout, text=query_text)
        ctx.fill()

        ctx.save()
        ctx.translate(-30, 0)
        common.context.text(ctx, self.current_state.layout, text=self.symbol)
        ctx.restore()

        ctx.fill()
        ctx.set_source_rgba(1, 1, 1, 0.35 + (self.current_state.cursor_transparency * 0.75))
        ctx.set_line_width(3)
        ctx.translate(5 - 1.5, 0)
        ctx.move_to(text_bounds.width, 5)
        ctx.line_to(text_bounds.width, self.current_state.input_bar_height * 0.8)
        ctx.stroke()
        ctx.restore()

        ctx.restore()
        # self.current_state.query.get_bounds()

class DMenu(EntryMenu):
    symbol = ">"

    def __init__(self, current_state):
        super().__init__(current_state)

    def entry_update(self, dt):
        pass

    def draw(self, ctx):
        self.current_state.layout.set_font_description(INPUT_BAR_FONT)

        height = (self._sia.current() * 40) + 15
        static_height = (self.current_state.entries_len * 40) + 15

        ctx.set_source_rgba(0.2,0.2,0.2, pytweening.easeInOutQuad(self._rtt))

        abs_y = -height * 0.5
        static_abs_y = -static_height * 0.5

        common.context.rounded_rectangle(ctx, 0, abs_y, self.current_state.width, height, min(max(height, 40), 20))
        ctx.fill()

        for index, (entry, [entry_timer, entry_delay_timer, leave]) in \
                enumerate(self.entries.items()):

            entry_timer = pytweening.easeOutQuint(entry_timer)

            ctx.save()
            ctx.translate(15 - (200 * (1 - entry_timer)), static_abs_y + (40 * index))
            ctx.set_source_rgba(1, 1, 1, entry_timer)
            common.context.text(ctx, self.current_state.layout, entry.name)
            ctx.restore()

        self.input_bar_draw(ctx, height * 0.5 + 30)

class Main(Looper):
    def __init__(self):
        super().__init__()

        self._ct = 0 # cursor blink timer

        self.window = Window(WindowType.FullScreen)
            
        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw

        self.current_state = CurrentState()
        self.current_state.active_menu_type = MenuType.Shell
        self.current_state.query = Textbox()
        self.current_state.query.home_end_enabled = False
        self.current_state.searching = False
        self.current_state.loaded = False

        self.dmenu = DMenu(self.current_state)

        self.window.connect_animated_overlay(self.main_animator)
        self.window.create_window()
        self.window.connect('key_press_event', self.on_key_press)
        self.window.grab()
       
        self.loop_init()

    def contains_subquery(self, substring):
        return self.current_state.query.input in substring

    def search(self):
        if self.current_state.searching or not self.current_state.query.input.strip():
            return

        self.current_state.searching = True
        self.current_state.loaded = False

        menu_type = self.current_state.active_menu_type

        self.current_state.entries.clear()

        if menu_type == MenuType.Shell:
            entries = {}

            for path_dir in os.getenv('PATH').split(os.pathsep):
                if not os.path.isdir(path_dir):
                    continue

                for rel_file in os.listdir(path_dir):
                    file = os.path.join(path_dir, rel_file)

                    if not os.path.isfile(file) or not os.access(file, os.X_OK) or not self.contains_subquery(rel_file):
                        continue

                    new_entry = Entry()
                    new_entry.name = rel_file
                    entries[rel_file] = new_entry

            self.current_state.entries = list(entries.values())

        elif menu_type == MenuType.Dmenu:
            pass

        self.current_state.entries.sort(key=lambda item: item.name)
        self.current_state.total_entries_len = len(self.current_state.entries)
        self.current_state.entries_len = min(self.current_state.total_entries_len, self.current_state.view_size)
        self.current_state.entry_index = min(self.current_state.total_entries_len, self.current_state.entry_index)
        self.current_state.update_page() # i should prob use some sort of attr change/access function instead of this

        self.current_state.searching = False
        self.current_state.searched = True
        self.current_state.loaded = True

    def on_key_press(self, _, event):
        if event.hardware_keycode == 9:
            Gtk.main_quit()
            return True
        
        if event.hardware_keycode in [111, 116] and self.current_state.entries_len:
            self.current_state.entry_index = (self.current_state.entry_index \
                    + (1 if event.hardware_keycode == 116 else -1)) % \
                    self.current_state.total_entries_len
            self.current_state.update_page()
        elif event.hardware_keycode == 36:
            if not self.current_state.searching:
                t = Thread(target=self.search)
                t.daemon = True
                t.start()
        else:
            self.current_state.query.handle_event(event)

        return True

    def update(self, dt):
        self._ct = (self._ct + dt * 4) % 2
        
        self.current_state.cursor_transparency = pytweening.easeOutQuad(\
                self._ct if self._ct < 1 else (1 - (self._ct - 1)))

        self.dmenu.update(dt)
        self.main_animator.draw()

    def draw(self, ctx, width, height):
        if self.current_state.layout is None:
            self.current_state.layout = PangoCairo.create_layout(ctx)

        ctx.translate((width * 0.5) - (self.current_state.width * 0.5), height * 0.5)
        self.dmenu.draw(ctx)

