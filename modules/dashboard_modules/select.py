import os
import subprocess
from modules.dashboard_modules.util import Widget

root = os.path.dirname(__file__) + '/../..'

MAIN_COMMAND = os.path.join(root, 'unfluiid')

class Choice:
    _st = 0
    selected_timer = 0

    def __init__(self, icon, text, command):
        if isinstance(command, str):
            command = [command]

        self.icon = icon
        self.text = text
        self.command = command

class SelectWidget(Widget):
    choices = [
        Choice('>', 'execute', [''])
    ]

    def __init__(self):
        super().__init__(width=350, height=300)

    def draw_widget(self, ctx, layout):
        ctx.translate(-self.padding, -self.padding)

    def draw_background(self, ctx):
        pass # transparent
