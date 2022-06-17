from socket import AI_PASSIVE
from components.looper import Looper
from components.window import Window, WindowType
from components.animator import Animator

import gi
gi.require_version('Rsvg', '2.0')
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Gtk, Rsvg, Pango, PangoCairo

import os
import common.context
import pytweening

import cairo
from cairo import ImageSurface

from xdg import DesktopEntry
from xdg.Exceptions import ValidationError, ParsingError
from xdg.IconTheme import getIconPath

class CurrentState: # struct :trollface:
    query = ""
    cursor_position = 0
    layout = None

    input_bar_font = Pango.FontDescription("Iosevka Term 30")

    width = 800
    global_alpha = 0
    desktop_session = os.getenv("DESKTOP_SESSION")
    entries = []
    executable_entries = []
    search_entries = []

    _ct = 0 # cursor blink time (1-2)
    p_ct = 0 # cursor blink time (1-2)

svg_handler = Rsvg.Handle()
ascii_range = range(32, 129)

class Entry(DesktopEntry.DesktopEntry):
    def __init__(self, path):
        super().__init__(path)

        self.name = self.getName()
        self.generic_name = self.getGenericName()
        self.comment = self.getComment()
        self.exec = self.getExec()
        
        for sub in ['%F', '%f', '%U', '%u']:
            self.exec = self.exec.replace(sub, '')

        self.icon_path = getIconPath(self.getIcon())

        if self.icon_path is not None:
            _, self.ext = os.path.splitext(self.icon_path)
            
            if self.ext == '.png':
                self.icon = ImageSurface.create_from_png(self.icon_path)
            elif self.ext == '.svg':
                self.icon = svg_handler.new_from_file(self.icon_path)

    def can_show(self, current_state):
        show_in = self.getOnlyShowIn()

        return not self.getHidden() and not self.getNoDisplay() \
                and current_state.desktop_session not in self.getNotShowIn() \
                and (not show_in or current_state.desktop_session in show_in)


class EntryContainer:
    def __init__(self, current_state):
        self.current_state = current_state
        self.dsp_text = ""
        self.cursor_text = "" # cursor position lol

        self.cursor_position = 0
        self.target_position = 0 

    _non_selected_color = (214/255, 96/255, 70/255)
    _search_symbol = ""
    _out_of_bounds = 36

    def get_dsp_query(self):
        offset = max(((self.current_state.cursor_position - 1) // self._out_of_bounds) * self._out_of_bounds, 0)
        
        return self.current_state.query[offset:self._out_of_bounds+offset]

    def update(self, dt):
        self.dsp_text = self.get_dsp_query()
        # self.cursor_position += ((self.target_position) - self.cursor_position) * (dt * 20)

    def draw(self, ctx):
        self.input_bar_draw(ctx)

    def input_bar_draw(self, ctx):
        ctx.set_source_rgba(0.225, 0.225, 0.225, self.current_state.global_alpha)
        
        common.context.rounded_rectangle(ctx, 0, -30, self.current_state.width, 60, 25)
        ctx.fill()

        ctx.save()
        ctx.set_source_rgba(1, 1, 1, self.current_state.global_alpha)
        ctx.translate(12.5, 20)
        ctx.set_font_size(60)
        ctx.select_font_face("Iosevka Term")
        ctx.show_text(self._search_symbol)
        ctx.fill()
        ctx.restore()


        ctx.save()
        ctx.set_source_rgba(1, 1, 1, self.current_state.global_alpha * \
                self.current_state.p_ct)
        
        ctx.move_to(58 + self.cursor_position, -20)
        ctx.line_to(58 + self.cursor_position, 20)
        ctx.stroke()

        ctx.set_source_rgba(1, 1, 1, self.current_state.global_alpha)
        ctx.translate(55, -25)
        self.current_state.layout.set_font_description(self.current_state.input_bar_font)
        common.context.text(ctx, self.current_state.layout, self.dsp_text)
        self.current_state.layout.set_text(self.dsp_text, -1) # TODO: fix cursor position when on previous page from the last
        self.cursor_position = self.current_state.layout.get_pixel_size().width

        
        # self.target_position = w
        ctx.fill()

        ctx.restore()
        

class Main(Looper):
    def __init__(self):
        super().__init__()

        self.current_state = CurrentState()
       
        path_directories = os.getenv('PATH').split(os.pathsep)
        
        # for directory in path_directories:
        #    try:
        #        for file in os.listdir(directory):
        #            full_path = os.path.join(directory, file) 

        #            if file in self.current_state.executable_entries or not os.path.isfile(full_path) or not os.access(full_path, os.X_OK):
        #                continue

        #            self.current_state.executable_entries.append(file)
        #    except FileNotFoundError:
        #        pass

        #for path in os.listdir('/usr/share/applications'):
        #    try:
        #        new_entry = Entry(os.path.join('/usr/share/applications', path))
        #        new_entry.validate()
#
#                if not new_entry.can_show(self.current_state):
#                    continue
#
#                self.current_state.entries.append(new_entry)
#            except (ValidationError, ParsingError):
#                pass

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
        self.current_state._ct = (self.current_state._ct + dt * 1.5) % 2
        self.current_state.p_ct = pytweening.easeOutQuad(self.current_state._ct \
                if self.current_state._ct < 1 else (1 - (self.current_state._ct - 1)))

        self.container_test.update(dt)
        self.main_animator.draw()

    def draw(self, ctx, width, height):
        if self.current_state.layout is None:
            self.current_state.layout = PangoCairo.create_layout(ctx)

        _at = pytweening.easeInOutQuad(self._at)
        self.current_state.global_alpha = _at
        ctx.translate((width * 0.5) - (600 * (1 - _at)) - (self.current_state.width * 0.5), height * 0.5)
        self.container_test.draw(ctx)

    def on_key_press(self, _, event):
        keycode = event.hardware_keycode
        keyval = event.keyval
        string = event.string
        
        if keycode == 9:
            Gtk.main_quit()
            return True

        # print(keycode)
        
        if keycode == 110:
            self.current_state.cursor_position = 0
        elif keycode == 115:
            self.current_state.cursor_position = len(self.current_state.query)
        if keycode in [113, 114]:
            self.current_state.cursor_position = min(max(self.current_state.cursor_position + (\
                    -1 if keycode == 113 else 1), 0), len(self.current_state.query))
        elif keyval == 65288:
            self.current_state.query = self.current_state.query[:-1]
        elif keyval in ascii_range:
            at_last = self.current_state.cursor_position == len(self.current_state.query)

            if at_last:
                self.current_state.query += chr(keyval)
                self.current_state.cursor_position = len(self.current_state.query)
            else:
                self.current_state.query = self.current_state.query[0:self.current_state.cursor_position] \
                        + chr(keyval) + self.current_state.query[self.current_state.cursor_position:]

                self.current_state.cursor_position += 1

        return True

    
