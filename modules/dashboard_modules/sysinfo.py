from modules.dashboard_modules.util import Widget
import common.context

import psutil

import time
from time import perf_counter as get_time
import pytweening

from gi.repository import Pango

import cairo

TIME_FONT = Pango.FontDescription('Cantarell 50')
TIME_FONT.set_weight(Pango.Weight.BOLD)

SMALL_FONT = Pango.FontDescription('Cantarell 18')
SMALL_BOLD_FONT = Pango.FontDescription('Cantarell 18')
SMALL_BOLD_FONT.set_weight(Pango.Weight.BOLD)

T_NAMES = ['%H', '%M', '%S']

class SysTimeTranslate:
    exiting = False
    _at = 0 # appearance timer
    _et = 0 # exit timer

    _tat = 0
    _tet = 0

    dsp = ""

class SysInfoWidget(Widget):
    background_color = (200/255, 162/255, 152/255)

    def __init__(self):
        _w = 300

        super().__init__(1000 - _w, 0, _w, _w)
        self.start_x -= self.padding * 2

        self.t = ['00'] * 3 # i should've done this earlier dasfjiojifosdaoujidfsa 
        self.lt = None
        self.at = [[] for _ in range(3)]
        self.atrf = [None for _ in range(3)]

        self.update_status()

        self.update_time_timer = 0
        self.display_now = True

    def update_status(self):
        self.processes_running = len(list(psutil.process_iter()))
        self.percentage = psutil.virtual_memory().percent

    def update_timer_ui_layout(self):
        if self.lt is not None:
            pass
        
        for i, (at, t) in enumerate(zip(self.atrf, self.t)):
            if at is not None and at.dsp == t:
                continue

            new_at = SysTimeTranslate()
            new_at.dsp = t

            if self.display_now:
                new_at._at = 1

            if at is not None:
                at.exiting = True

            self.atrf[i] = new_at
            self.at[i].append(new_at)
        
        self.display_now = False
        self.lt = self.t.copy()

    def update_widget(self, dt):
        if self.update_time_timer <= 0:
            for i, name in enumerate(T_NAMES):
                self.t[i] = time.strftime(name)
            
            self.update_timer_ui_layout()

            ct = get_time()
            self.update_time_timer = ct - round(ct)
        else:
            self.update_time_timer -= dt

        for i, ats in enumerate(self.at):
            new_ats = []

            for at in ats:
                at._at = min(at._at + dt * 2.35, 1)
                at._tat = pytweening.easeInOutQuad(at._at)
                at._tet = pytweening.easeInOutQuad(at._et)

                if at.exiting:
                    at._et = min(at._et + dt * 2.35, 1)

                    if at._et < 1:
                        new_ats.append(at)
                else:
                    new_ats.append(at)

            self.at[i] = new_ats
  
    def circle(self, ctx, layout, header, percentage, x=0, y=0, radius=50):
        ctx.save()
        ctx.set_source_rgb(0.25, 0.25, 0.25)
        ctx.set_line_width(10)
        ctx.set_line_cap(cairo.LineCap.ROUND)
        common.context.circle(ctx, x, y, radius)
        ctx.stroke()
        ctx.restore()

    def draw_widget(self, ctx, layout):
        ctx.set_source_rgb(0, 0, 0)

        layout.set_font_description(TIME_FONT)

        ctx.save()
        ctx.rectangle(0, 0, self.width, 60)
        ctx.clip()

        for i, ats in enumerate(self.at):
            for at in ats:
                ctx.save()
                w = common.context.text_bounds(layout, at.dsp).width * 0.5

                ctx.translate((45 + (i * 90)) - w, ((1 - at._tat) * 100) + (at._tet * -100) - 10)
                common.context.text(ctx, layout, at.dsp)
                ctx.fill()
                ctx.restore()

        ctx.restore()

        layout.set_font_description(SMALL_FONT)

        ctx.save()
        ctx.translate(10, 65) 
        common.context.text(ctx, layout, f"processes:")
        ctx.move_to(120, 0)
        layout.set_font_description(SMALL_BOLD_FONT)
        common.context.text(ctx, layout, str(self.processes_running))
        ctx.restore()

        self.circle(ctx, layout, "test", 50, 65, 170)
