import os
import subprocess
from modules.dashboard_modules.util import Widget
import pytweening

root = os.path.dirname(__file__) + '/../..'

MAIN_COMMAND = os.path.join(root, 'unfluiid')

import common.context
from gi.repository import Pango

FONT = Pango.FontDescription('Cantarell 30')
ICON_FONT = Pango.FontDescription('Iosevka Term 30')

class Choice:
    _st = 0
    selected_timer = 0

    def __init__(self, icon, text, command):
        if isinstance(command, str):
            command = [command]

        self.icon = icon
        self.text = text
        self.command = command

    def execute(self):
        subprocess.Popen([MAIN_COMMAND] + self.command, stdout=subprocess.DEVNULL, stdin=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL, cwd=os.path.expanduser('~'))

class SelectWidget(Widget):
    choices = [
        Choice('', 'search', ['search']),
        Choice('>', 'execute', ['search', 'execute_shell']),
        Choice('⏻', 'powermenu', ['powermenu'])
    ]

    choice_height = 97.5

    _start_background_color = (0.2, 0.2, 0.2)
    _selected_background_color = (242/255, 166/255, 150/255)
    _diff_background_color = (
                _selected_background_color[0] - _start_background_color[0],
                _selected_background_color[1] - _start_background_color[1],
                _selected_background_color[2] - _start_background_color[2],
            )

    def __init__(self):
        super().__init__(width=350, height=300)

        self.entered = False
        self.no_zoom = True
        self.select_index = 0

    def update_widget(self, dt):
        for i, choice in enumerate(self.choices):
            # choice._st = max(min(choice._st + dt * (5 if i == self.select_index else -5), 1), 0)
            choice.selected_timer += ((i == self.select_index) - choice.selected_timer) * (dt * 20)

    def on_key_press(self, event):
        if event.hardware_keycode in [111, 116]:
            self.select_index = (self.select_index + (1 if event.hardware_keycode \
                    == 116 else -1)) % len(self.choices)
        elif event.hardware_keycode == 36 and self.main_widget.zoomed_widget is None:
            self.entered = True
            self.main_widget.quit()

    def on_quit(self):
        if not self.entered:
            pass

        self.choices[self.select_index].execute()

    def draw_widget(self, ctx, layout):
        ctx.translate(-self.padding, -self.padding)
        
        for i, choice in enumerate(self.choices):
            ctx.save()
            _stscl = 1 - (choice.selected_timer * 0.2)
            ctx.translate(30 * choice.selected_timer, (i * (self.choice_height + 5)) + (8 * choice.selected_timer))
            ctx.set_source_rgba(
                    self._start_background_color[0] + self._diff_background_color[0] * choice.selected_timer,
                    self._start_background_color[1] + self._diff_background_color[1] * choice.selected_timer,
                    self._start_background_color[2] + self._diff_background_color[2] * choice.selected_timer,
                    self.alpha)
            ctx.scale(_stscl, _stscl)

            common.context.rounded_shadow(ctx, 0, 0, self.width, self.choice_height, radius=20, width_offset=20, height_offset=20,
                    global_alpha=self.alpha*choice.selected_timer, color=self._selected_background_color)

            common.context.rounded_rectangle(ctx, 0, 0, self.width, self.choice_height, 20)

            ctx.fill()
            _tc = 1 - choice.selected_timer
            ctx.set_source_rgba(_tc, _tc, _tc, self.alpha)
            
            ctx.save()
            layout.set_font_description(ICON_FONT)
            ctx.move_to(30, 20)

            common.context.text(ctx, layout, choice.icon)

            layout.set_font_description(FONT)
            ctx.move_to(70, 20)
            
            common.context.text(ctx, layout, choice.text)

            ctx.move_to(0,0)
            ctx.restore()

            ctx.restore()

    def draw_background(self, ctx):
        pass # transparent
