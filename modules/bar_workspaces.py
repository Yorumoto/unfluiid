import cairo
import common.context
import os
import pytweening
from i3ipc.events import Event

from components.tween import DeltaTween

import gi
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo

class WorkspaceCircle:
    def __init__(self):
        self._at = 0 # appearance timer
        self._atb = False # first appearance?

        self._ft = 0 # focus timer
        self._sdt = 0 # start delay timer (initialize animation)
        self._t = ""
        
        self.urgent = False
        self._ut = 2 # urgent timer

    def update(self, dt, disappearing, is_focused, workspace):
        if self._ut <= 2:
            self._ut = min(self._ut + dt * 1.75, 2)

            if self._ut >= 2 and self.urgent:
               self._ut = 0 

        if disappearing:
            self._at = max(self._at - dt * 3, 0)
            self._ft = max(self._ft - dt * 3, 0)
        else:
            self._t = str(workspace.num)
            self._ft = max(min(self._ft + (dt * (8 if is_focused else -8)), 1), 0) # clamp lol

            if self._sdt > 0:
                self._sdt -= dt
            else:
                self._at = min(self._at + dt * 3, 1)

                if self._at >= 1 and self._atb:
                    self._atb = False

    def draw(self, ctx, x, height):
        _at = pytweening.easeInOutQuad(self._at)

        _ut = pytweening.easeOutQuad(self._ut if self._ut < 1 else 1 - (self._ut - 1)) # translated urgent timer
        ctx.set_source_rgba(1.0, 1.0 - _ut, 1.0 - _ut, _at)

        line_width = 2 + (self._ft * 15)
        ctx.set_line_width(line_width)

        common.context.circle(ctx, x, (height * 0.5), ((height * 0.35) - (line_width * 0.5)) * _at)
        ctx.stroke()
        
        r = 1 - self._ft
        ctx.set_source_rgba(r, r, r, _at)
        ctx.save()
        ctx.translate(x - (2.75 + ((len(self._t)-1) * 3)), (height * 0.5) + 4)
        ctx.show_text(self._t) 
        ctx.restore()

        return (height * 1) * (_at if not self._atb else 1) 

class Main:
    WORKSPACES_MAX = 10

    focused_placeholder = "the coolest wallpaper"

    def __init__(self, i3_connection):
        self.layout = None

        self.i3_connection = i3_connection
        self.i3_connection.on(Event.WORKSPACE_FOCUS, self.on_workspace_focus)
        self.i3_connection.on(Event.WINDOW_TITLE, self.on_window_update_title)
        self.i3_connection.on(Event.WINDOW_FOCUS, self.on_window_update_title)
        self.i3_connection.on(Event.WINDOW_CLOSE, self.on_window_update_title)
        self.i3_connection.on(Event.WINDOW_URGENT, self.urgent)

        self.focused_window_name = None

        self.update_workspaces()
        self.on_window_update_title()

        self.workspace_circles = [WorkspaceCircle() for _ in range(self.WORKSPACES_MAX+1)]
        
        self.layout_description = Pango.FontDescription("Iosevka Term 15")
        self.layout = None

        # for i in range(self.i3_workspaces+1):
        for i, workspace in enumerate(self.workspaces):
            self.workspace_circles[workspace.num]._sdt = (i) * (0.125 * 0.75)
            self.workspace_circles[workspace.num]._atb = True
       
        self.title_tweening = False
        self.title_tweening_new_passed = False
        self._tt = 0 # title time (1-2)

        self._view_workspaces = 1
        self._int_view_workspaces = 1
        self._wpt = DeltaTween(target=self.i3_workspaces) # messy lol
        self._lvtr = 0

    def urgent(self, _, window):
        try:
            workspace_num = self.i3_connection.get_tree().find_by_id(window.ipc_data['container']['id']).workspace().num
            workspace_circle = self.workspace_circles[workspace_num]
            workspace_circle.urgent = True

            if workspace_circle._ut >= 2:
                workspace_circle._ut = 0
        except (IndexError, AttributeError): # attributeerror my ass
            pass

    def get_focused(self):
        return self.i3_connection.get_tree().find_focused()
        
    def update_workspaces(self):
        focused = self.get_focused()
        self.workspaces = self.i3_connection.get_workspaces()
        self.i3_workspaces = len(self.workspaces)

        # broken lol
        # self.focused_workspace = min(focused.workspace().num, self.i3_workspaces)
        
        try:
            # self.focused_workspace = [x.num for x in self.workspaces].index(focused.workspace().num) + 1
            self.focused_workspace = focused.workspace().num

            try:
                self.workspace_circles[self.focused_workspace].urgent = False
            except AttributeError:
                pass
        except IndexError:
            pass

    def on_window_update_title(self, *_):
        focused = self.get_focused()

        try:
            self.new_focused_window_name = self.focused_placeholder if int(focused.name) else focused.name
        except (ValueError, TypeError):
            try:
                self.new_focused_window_name = (focused.name[0:40] + "...") if len(focused.name) >= 40 else focused.name
            except TypeError:
                self.new_focused_window_name = self.focused_placeholder

        if self.focused_window_name is None:
            self.focused_window_name = self.new_focused_window_name
        elif self.focused_window_name != self.new_focused_window_name and not self.title_tweening:
            self.title_tweening = True
            self.title_tweening_new_passed = False
            self._tt = 0

    def on_workspace_focus(self, _, new_workspace):
        self.update_workspaces()
        _view_workspaces = self.i3_workspaces
       
        if self._int_view_workspaces != _view_workspaces:
            self._wpt.change_target(_view_workspaces)
        
        self._int_view_workspaces = _view_workspaces
        self.on_window_update_title()

    def update(self, dt):
        if self.title_tweening:
            self._tt = min(self._tt + dt * 7.5, 2)

            if self._tt >= 1 and not self.title_tweening_new_passed:
                self.focused_window_name = self.new_focused_window_name
                self.title_tweening_new_passed = True

            if self._tt >= 2:
                self.title_tweening = self.new_focused_window_name != self.focused_window_name
                self._tt = 0

                if self.title_tweening:
                    self.title_tweening_new_passed = False

        self._wpt.update(dt * 4)
        self._view_workspaces = self._wpt.current()
 
        if self._lvtr < 1:
            self._lvtr = min(self._lvtr + dt * 3, 1)

        # for i, circle in enumerate(self.workspace_circles):
        #    if i + 1 <= self.i3_workspaces:
        #        workspace = self.workspaces[i]
        #        circle.update(dt, i + 1 > self.i3_workspaces, workspace.num == self.focused_workspace, workspace)
        #    else:
        #       circle.update(dt, True, i == self.focused_workspace, None)

        workspace_circles = set(self.workspace_circles)

        for i, workspace in enumerate(self.workspaces):
            circle = self.workspace_circles[workspace.num]
            circle.update(dt, False, workspace.num == self.focused_workspace, workspace)

            if circle in workspace_circles:
                workspace_circles.discard(circle)

        for circle in workspace_circles:
            circle.update(dt, True, False, None)

    def draw(self, context, height):
        # if self.layout is None:
        #    self.layout = PangoCairo.create_layout(context)
        #    self.layout.set_font_description(Pango.FontDescription(f'Cantarell {int(height - 5)}'))

        if self.layout is None:
            self.layout = PangoCairo.create_layout(context)

        _lvtr = pytweening.easeInOutQuad(self._lvtr)
        context.set_source_rgba(0.2, 0.1, 0.3, 0.75 * _lvtr)

        common.context.rounded_rectangle(context, 0, 0, self._view_workspaces * height, height, height * 0.5)
        context.fill()
         
        x = height * 0.5

        for circle in self.workspace_circles:
            x += circle.draw(context, x, height)
        
        text_tt = pytweening.easeOutQuad((1 - self._tt) if self._tt <= 1 else (self._tt - 1))

        context.set_source_rgba(0.2, 0.1, 0.3, 0.75 * (_lvtr) * text_tt)
        
        context.set_font_size(20)

        # self.layout.set_text(self.focused_window_name, -1)
        extents = self.layout.get_pixel_size()

        common.context.rounded_rectangle(context, (self._view_workspaces * height) + 5, 0, extents.width + 30, height, height * 0.5)
        context.fill()
        context.save()
        context.translate(self._view_workspaces * height + 15, 5)
        context.set_source_rgba(1, 1, 1, text_tt * _lvtr)
      
        self.layout.set_font_description(self.layout_description)
        common.context.text(context, self.layout, self.focused_window_name)
        
        context.stroke()
        context.restore()
       
        # influence the font to others
        context.select_font_face("Iosevka Term", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

