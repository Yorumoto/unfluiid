from components.window import Window, WindowType
from components.textbox import Textbox
from components.animator import Animator
from components.looper import Looper
from components.tween import DeltaTween

import shutil
import shlex
import subprocess

from math import pi
from xdg import Exceptions as XdgExceptions
from xdg import DesktopEntry, IconTheme

from enum import Enum
from threading import Thread

from random import randint

import pytweening
import common.context

import gi
gi.require_version('Rsvg', '2.0')
from gi.repository import Gtk, GLib, Pango, PangoCairo, Rsvg

import cairo
GLib.threads_init()

import time
import os

INPUT_BAR_FONT = Pango.FontDescription("Iosevka Term 25")
LIST_NUMBER_FONT = Pango.FontDescription("Iosevka Term 14")

DESKTOP_FONT_SMALL = Pango.FontDescription("Cantarell Regular 11")
DESKTOP_FONT_MAIN = Pango.FontDescription("Cantarell Regular 22")

class MenuType(Enum):
    Unknown = -1
    Shell = 0
    Dmenu = 1

class CurrentState:
    input_bar_height = 50
    layout = None
   
    abs_empty = False

    entries = []
    entries_len = 0 # update
    total_entries_len = 0 # update pls
    
    entry_index = 0
    selected_entry_index = 0 # it's ALWAYSSS THE FIRST ITEM WITHOUT HTIS
    entry_page = 0

    current_menu = None

    cursor_transparency = 0
    loaded_transparency = 0

    appearance_timer = 0

    _list_exited = False
    _at = 0

    can_execute = False
    exiting = False

    searched = False
    searching = False
    loaded = False
    in_query_typing = False
    
    notified_of_change = False

    view_size = 10

    width = 800
    query : Textbox
    last_query = ""

    cache = {}
    
    exit_timer = 0

    def go_empty_state(self): 
        # self.exit_timer = bool(self.loaded and self.entries)

        self.loaded = False
        
        self.entry_index = 0
        self.total_entries_len = 0
        self.notified_of_change = True
        # self.entries_len = 0

    def start_search(self):
        self.entries.sort(key=lambda item: (len(item.name), item.name))
        self.total_entries_len = len(self.entries)
        self.entries_len = min(self.total_entries_len, self.view_size)
        self.entry_index = min(max(self.total_entries_len - 1, 0), self.entry_index)

        self.update_page() # i should prob use some sort of attr change/access function instead of this
        self.searching = True
        self.loaded = False

    def finish_search(self):
        self.searching = False
        self.searched = True
        self.loaded = True
        self.in_query_typing = False
        self.notified_of_change = self.last_query != \
                self.query.input
        self.last_query = self.query.input

    def exit(self):
        if self.exiting:
           return 

        self.query.input_disabled = True
        self.exiting = True
        self.go_empty_state()

    def execute(self):
        self.selected_entry_index = self.entry_index
        self.exit()
        self.can_execute = True

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

    execute = ""

    icon = None

    run_via_terminal = False

    cache = {}

class AnimatableEntry: 
    leaving = False
    selected = False

    start_y = 0
    index = 0
        

    _at = 0 # appearance timer
    _del_t = 0 # appearance delay timer
    _st = 0 # selected timer

 
class EntryIconImageType(Enum):
    Unknown = -1
    PNG = 0
    SVG = 1

class EntryIcon:
    format_type = EntryIconImageType.Unknown
    icon = None
    width = 0
    height = 0

class EntryMenu:
    symbol = ""
    background = (0.22, 0.215, 0.22)
    
    def __init__(self, current_state):
        self.current_state = current_state
        
        self.ready_to_scroll = True

        self.abs_y = None
        self.static_abs_y = None
        self.first_entry = None

        self.test = 0

        self._sia = DeltaTween(target=0)
        self._rtt = 0 # results transparency timer
        
        self.entries = {} # [EntryObject] -> [EntryShiftTimer, EntryShiftDelayTimer, IsLeaving, RelativeIndex]
        # pls add RelativeIndex
        
        self.page_offset = 0
        self.last_page = None
        self.last_entries_len = None
 
    def update(self, dt):
        page = self.current_state.entry_page
        entries_len = self.current_state.entries_len

        if self.static_abs_y and self.current_state.notified_of_change \
                or (entries_len != self.last_entries_len or page != self.last_page):
            start, end = self.current_state.get_page_offset()
            self.page_offset = start

            page_entries = self.current_state.entries[start:end]

            for entry, animatable in self.entries.items():
                # animatable._del_t = animatable.index * 0.025 if animatable._at >= 1 else 0
                animatable.start_y = self.static_abs_y
                animatable.leaving = True

            if self.current_state.loaded:
                self.first_entry = None

                for index, entry in enumerate(page_entries):
                    new_animatable = AnimatableEntry()
                    new_animatable.index = index
                    # i kinda don't like the adding each item slowly one by one, it looks kinda slow
                    # new_animatable._del_t = index * 0.0175

                    if self.first_entry is None:
                        self.first_entry = new_animatable

                    self.entries[entry] = new_animatable
                
            self._sia.change_target(entries_len)
            self.current_state.notified_of_change = False

        self._sia.update(dt * 4)
        self._rtt = max(min(self._rtt + (dt * (16 if self.current_state.entries_len \
                and self.current_state.loaded else -16)), 1), 0)
        
        # new_entries = {}
        
        animatable_entry_items = list(self.entries.items())

        for (entry, animatable) in animatable_entry_items:
            animatable.selected = animatable.index == self.current_state.entry_index - self.page_offset

            if animatable._del_t > 0:
                animatable._del_t -= dt
            else:
                animatable._at = max(min(animatable._at + dt * (-2.5 if animatable.leaving else 2.5), 1), 0)

            animatable._st = max(min(animatable._st + dt * (-9 if (animatable.selected and not animatable.leaving) else 9), 1), 0)
            
            if animatable.leaving and animatable._at <= 0:
                del self.entries[entry]
 
        self.ready_to_scroll = (not self.first_entry.leaving and self.first_entry._at > 0.8) if \
                self.first_entry is not None else True


        # self.entries = new_entries
        

        self.last_entries_len = entries_len
        self.last_page = self.current_state.entry_page

    def draw(self, ctx):
        pass

    def input_bar_draw(self, ctx, offset):
        ctx.save()
        _at = self.current_state.appearance_timer

        ctx.translate((1 - _at) * -400, -offset)

        ctx.set_source_rgba(*self.background, _at)
        
        common.context.rounded_shadow(ctx, 0, -self.current_state.input_bar_height * 0.5, self.current_state.width, self.current_state.input_bar_height, 
                20, width_offset=15, height_offset=15, color=(0.1, 0.1, 0.1), global_alpha=_at)

        common.context.rounded_rectangle(ctx, 0, -self.current_state.input_bar_height * 0.5, self.current_state.width, self.current_state.input_bar_height, 20)
        ctx.fill()
        
        ctx.set_source_rgba(1, 1, 1, _at)

        self.current_state.layout.set_font_description(INPUT_BAR_FONT)

        (query_start, query_end), rel_cursor_position = self.current_state.query.get_bounds(44)
        query_text = self.current_state.query.input[query_start:query_end]
        text_bounds = common.context.text_bounds(self.current_state.layout, self.current_state.query.input[:rel_cursor_position]) 
        
        ctx.save()
        ctx.translate(45, -20)
        common.context.text(ctx, self.current_state.layout, text=query_text)
        ctx.fill()

        ctx.save()


        ctx.set_source_rgba(1, 1, 1, _at)
        ctx.translate(-27, 0)
        common.context.text(ctx, self.current_state.layout, text=self.symbol)
        ctx.fill()
        ctx.restore()

        ctx.set_source_rgba(1, 1, 1, (0.35 + (self.current_state.cursor_transparency * 0.75)) * _at)
        ctx.set_line_width(3)
        ctx.translate(5 - 1.5, 0)
        ctx.move_to(text_bounds.width, 5)
        ctx.line_to(text_bounds.width, self.current_state.input_bar_height * 0.8)
        ctx.stroke()
        ctx.restore()

        ctx.restore()
        # self.current_state.query.get_bounds()

START_CIRCLE = -90 * (pi / 180)
DOUBLE_PI = pi * 2

class DMenu(EntryMenu):
    menu_type = MenuType.Dmenu

    def __init__(self, current_state):
        super().__init__(current_state)

    _normal_colors = (214/255, 96/255, 70/255)
    _selected_colors = (242/255, 166/255, 150/255)
    
    _diff_colors = (
        _selected_colors[0] - _normal_colors[0],
        _selected_colors[1] - _normal_colors[1],
        _selected_colors[2] - _normal_colors[2],
    )

    entry_height = 80
    fit_icon_size = 64

    def draw(self, ctx):
        height = (self._sia.current() * self.entry_height) + 15
        static_height = (self.current_state.entries_len * self.entry_height) + 15

        _rtt = pytweening.easeInOutQuad(self._rtt) * self.current_state.appearance_timer

        ctx.set_source_rgba(0.2,0.2,0.2, _rtt)

        self.abs_y = -height * 0.5
        self.static_abs_y = -static_height * 0.5

        radius= min(max(height, 40), 20)

        common.context.rounded_shadow(ctx, 0, self.abs_y, self.current_state.width, height + 50, radius, 
                global_alpha=_rtt, color=(0.125, 0.125, 0.125))

        common.context.rounded_rectangle(ctx, 0, self.abs_y, self.current_state.width, height + 50, radius)
        ctx.fill()

        ctx.save()
        ctx.translate(15, self.abs_y + height)
        ctx.set_source_rgba(1, 1, 1, _rtt)
        self.current_state.layout.set_font_description(INPUT_BAR_FONT)
       
        common.context.text(ctx, self.current_state.layout, 
                f"{self.current_state.entry_index+1}/{self.current_state.total_entries_len}")
        
        ctx.move_to(self.current_state.width - 30, 0)

        if self.current_state.entries:
            right_text = self.current_state.entries[self.current_state.entry_index].name
            text = common.context.text_bounds(self.current_state.layout, right_text)
            ctx.move_to(self.current_state.width - 40 - text.width, 0)
            common.context.text(ctx, self.current_state.layout, right_text)

        self.current_state.layout.set_alignment(Pango.Alignment.LEFT)

        ctx.fill()
        ctx.restore()

        
        for entry, animatable in self.entries.items():
            _at = pytweening.easeInOutQuint(animatable._at)
            _st = 1 - animatable._st
            # _sst = pytweening.easeInOutQuad(_st)

            ctx.save()
            ctx.translate(10 - (300 * (1 - _at)), 10 + (animatable.start_y or self.static_abs_y) + \
                    (self.entry_height * animatable.index))
            
            context_color = (
                self._normal_colors[0] + (self._diff_colors[0] * _st),
                self._normal_colors[1] + (self._diff_colors[1] * _st),
                self._normal_colors[2] + (self._diff_colors[2] * _st),
            )

            ctx.set_source_rgba(*context_color, _at)

            if _st > 0.5:
                common.context.rounded_shadow(ctx, 0, 0, self.current_state.width-20, self.entry_height-5, 15, 
                        width_offset=15, height_offset=15, 
                        color=self._selected_colors, global_alpha=_at*_st)

            common.context.rounded_rectangle(ctx, 0, 0, self.current_state.width-20, self.entry_height-5, 15)

            ctx.fill()
            
            ctx.set_source_rgba(0, 0, 0, _at)
            
            self.current_state.layout.set_font_description(DESKTOP_FONT_MAIN)

            shift_x = 80 if entry.icon else 20

            if entry.icon:
                ctx.save()

                if entry.icon.format_type == EntryIconImageType.SVG: # svg
                    # TODO: is there any way i can render svgs with alpha
                    # ctx.push_group()
                    # entry.icon.icon.render_cairo(ctx)
                    # pattern = ctx.pop_group()
                    # ctx.mask(pattern)
                    pass
                elif entry.icon.format_type == EntryIconImageType.PNG: # png
                    ctx.scale(self.fit_icon_size / entry.icon.width, self.fit_icon_size / entry.icon.height)
                    # icon_width = min(icon_width, self.fit_icon_size)
                    # icon_height = min(icon_height, self.fit_icon_size)
                    ctx.translate(
                        (40 * (entry.icon.width / self.fit_icon_size)),
                        (self.entry_height * 0.5 * (entry.icon.height / self.fit_icon_size)) - 2
                    )

                    ctx.set_source_surface(entry.icon.icon, -(entry.icon.width * 0.5), -(entry.icon.height * 0.5))
                    ctx.paint_with_alpha(_at)

                ctx.restore()

            ctx.save()

            ctx.move_to(shift_x, 2)
            common.context.text(ctx, self.current_state.layout, f"<b>{entry.name}</b>", markup=True)
            ctx.fill()

            self.current_state.layout.set_font_description(DESKTOP_FONT_SMALL)

            ctx.move_to(shift_x + 2, 37)
            common.context.text(ctx, self.current_state.layout, entry.short_description or entry.description)

            # don't overload user information!!
            # if entry.description:
            #    ctx.move_to(shift_x + 2, 54 if entry.short_description else 37)
            #    common.context.text(ctx, self.current_state.layout, f"{entry.description}")

            ctx.restore()

            ctx.restore()

        self.input_bar_draw(ctx, height * 0.5 + 30)
        

    def contains_subquery(self, substring):
        return self.current_state.abs_empty or self.current_state.query.input.lower() in substring.lower()
   
    def execute(self):
        try:
            current_entry = self.current_state.entries[self.current_state.selected_entry_index]
            print(current_entry.name, current_entry.execute, self.current_state.entry_index)
            command = shlex.split(current_entry.execute)

            if current_entry.run_via_terminal:
                command = ['nohup', 'i3-sensible-terminal', '-e'] + command
            else:
                command = ['nohup'] + command

            subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except IndexError:
            pass # a chance

    def search(self):
        self.current_state.start_search()

        desktop_session = os.getenv('DESKTOP_SESSION')
        new_entries = []

        if not self.current_state.cache.get('d_entries'):
            self.current_state.cache['d_entries'] = {}
        
        if not self.current_state.cache.get('icons'):
            self.current_state.cache['icons'] = {}

        for rel_entry_filename in os.listdir('/usr/share/applications'):
            try:
                entry_filename = os.path.join('/usr/share/applications', rel_entry_filename)
                cached_desktop_entry = self.current_state.cache['d_entries'].get(rel_entry_filename)
                
                if cached_desktop_entry is None:
                    desktop_entry = DesktopEntry.DesktopEntry(entry_filename)
                else:
                    desktop_entry = cached_desktop_entry
                
                do_not_show_in = desktop_entry.getNotShowIn()
                only_show_in = desktop_entry.getOnlyShowIn()

                if not (not desktop_entry.getHidden() and
                        not desktop_entry.getNoDisplay() and\
                        (not do_not_show_in or desktop_session not in do_not_show_in) and \
                        (not only_show_in or desktop_session in only_show_in)): 
                    continue

                if cached_desktop_entry is None:
                    self.current_state.cache['d_entries'][rel_entry_filename] = desktop_entry
                
                entry_name = desktop_entry.getName() 
                
                if not self.contains_subquery(entry_name):
                    # i've thought of a concise way that fits in the guard clause statement
                    # but can't get it done there so i'll do this instead
                    entry_keywords = desktop_entry.getKeywords()
                
                    for keyword in entry_keywords:
                        if not self.contains_subquery(keyword.lower()):
                            continue
                        break
                    else:
                        continue

                cached_desktop_icon = self.current_state.cache['icons'].get(rel_entry_filename)
                desktop_icon = None
                
                if cached_desktop_icon is None:
                    abs_icon_path = IconTheme.getIconPath(desktop_entry.getIcon())

                    if abs_icon_path is not None:
                        _, ext = os.path.splitext(abs_icon_path)

                        if ext == '.png':
                            desktop_icon = EntryIcon()
                            desktop_icon.icon = cairo.ImageSurface.create_from_png(abs_icon_path)
                            desktop_icon.width = desktop_icon.icon.get_width()
                            desktop_icon.height = desktop_icon.icon.get_height()
                            desktop_icon.format_type = EntryIconImageType.PNG
                        elif ext == '.svg':
                            pass
                        #    desktop_icon = EntryIcon()

                        #    handle = Rsvg.Handle.new_from_file(abs_icon_path)
                        #    dimensions = handle.get_dimensions()

                        #    desktop_icon.icon = handle
                        #    desktop_icon.width = dimensions.width
                        #    desktop_icon.height = dimensions.height
                        #    desktop_icon.format_type = EntryIconImageType.SVG
                        else:
                            print(f"Unknown icon extension of {abs_icon_path}")

                    if desktop_icon is not None:
                        self.current_state.cache['icons'][rel_entry_filename] = desktop_icon
                else:
                    desktop_icon = cached_desktop_icon


                new_entry = Entry()
                new_entry.name = entry_name
                new_entry.icon = desktop_icon
                new_entry.short_description = desktop_entry.getGenericName()
                new_entry.description = desktop_entry.getComment()
                new_entry.run_via_terminal = desktop_entry.getTerminal()
                new_entry.execute = desktop_entry.getExec().replace("%U", "")\
                        .replace("%u", "").replace("%F", "").replace("%f", "")
                
                new_entries.append(new_entry)
                
            except (XdgExceptions.ParsingError, XdgExceptions.DuplicateGroupError, \
                    XdgExceptions.NoGroupError, XdgExceptions.DuplicateKeyError, \
                    XdgExceptions.NoKeyError):
                pass

        self.current_state.entries = new_entries
        self.current_state.entries.sort(key=lambda item: (len(item.name), item.name))
        self.current_state.total_entries_len = len(self.current_state.entries)
        self.current_state.entries_len = min(self.current_state.total_entries_len, self.current_state.view_size)
        self.current_state.entry_index = min(max(self.current_state.total_entries_len - 1, 0), self.current_state.entry_index)
        self.current_state.update_page() # i should prob use some sort of attr change/access function instead of this
      
        self.current_state.finish_search()

class Main(Looper):
    def __init__(self):
        super().__init__()

        self._ct = 0 # cursor blink timer

        self.window = Window(WindowType.FullScreen)
            
        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw

        self.current_state = CurrentState()
        self.current_state.query = Textbox()
        self.current_state.query.home_end_enabled = False
        self.current_state.searching = False
        self.current_state.loaded = False
        self.current_state.search_timer = 0

        self.shell_menu = ShellMenu(self.current_state)
        self.dmenu = DMenu(self.current_state)

        self.window.connect_animated_overlay(self.main_animator)
        self.window.create_window()
        self.window.connect('key_press_event', self.on_key_press)
        self.window.grab(no_pointer=True)
     
        self.current_state.current_menu = self.shell_menu

        self.menus = [self.dmenu, None]
        
        self.autostart_search_timer = 1
        self.loop_init()

    def update(self, dt):
        if self.autostart_search_timer <= 0:
            self.search()
            self.autostart_search_timer = 1e11
        else:
            self.autostart_search_timer -= dt

        self._ct = (self._ct + dt * 4) % 2
       
        self.current_state.cursor_transparency = pytweening.easeInOutQuad(\
                self._ct if self._ct < 1 else (1 - (self._ct - 1)))

        if self.current_state.exiting:
            if self.current_state.exit_timer <= 0:
                self.current_state._at = max(self.current_state._at + dt * -4, 0)

                if self.current_state._at <= 0:
                    if self.current_state.can_execute:
                        self.current_state.current_menu.execute()

                    Gtk.main_quit()
                    return
                
            else:
                self.current_state.exit_timer -= dt 
        else:
            self.current_state._at = min(self.current_state._at + dt * 4, 1)

        self.current_state.appearance_timer = pytweening.easeInOutQuad(self.current_state._at)
        
        self.dmenu.update(dt)
        self.main_animator.draw()

    def draw(self, ctx, width, height):
        if self.current_state.layout is None:
            self.current_state.layout = PangoCairo.create_layout(ctx)
            self.current_state.layout.set_markup

        ctx.fill()
        ctx.translate((width * 0.5) - (self.current_state.width * 0.5), height * 0.5)
        self.dmenu.draw(ctx)

    def on_key_press(self, _, event):
        if event.hardware_keycode == 9:
            self.current_state.exit()
            return True
       
        controlled = self.current_state.query.controlled(event)
        
        if controlled and event.hardware_keycode in range(10, 12):
            self.current_state.go_empty_state()
        elif event.hardware_keycode == 110:
            self.current_state.entry_index = 0 
            self.current_state.update_page()
        elif event.hardware_keycode == 115:
            self.current_state.entry_index = self.current_state.total_entries_len - 1
            self.current_state.update_page()
        elif event.hardware_keycode in [111, 116] and self.current_state.entries_len > 0 \
                and self.current_state.loaded:
            self.current_state.entry_index = (self.current_state.entry_index \
                    + (1 if event.hardware_keycode == 116 else -1)) % \
                    self.current_state.total_entries_len
            self.current_state.update_page()
        elif event.hardware_keycode in [36, 104] and not self.current_state.exiting:
            if self.current_state.in_query_typing:
                self.search()
            elif self.current_state.entries:
                self.current_state.execute()
        elif not self.current_state.searching and self.current_state.query.handle_event(event):
            self.current_state.in_query_typing = True
            self.autostart_search_timer = 1e99

        return True


    def search(self):
        if self.current_state.searching:
            return

        self.current_state.abs_empty = not self.current_state.query.input
        searching_thread = Thread(target=self.current_state.current_menu.search)
        # searching_thread.daemon = True
        searching_thread.run()
