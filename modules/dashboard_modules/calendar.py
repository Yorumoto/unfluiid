import calendar
from datetime import date, datetime

from modules.dashboard_modules.util import Widget

import common.context
from gi.repository import Pango

HEADER_FONT = Pango.FontDescription('Cantarell 33')
HEADER_FONT.set_weight(Pango.Weight.BOLD)
HEADER_LIGHT_FONT = Pango.FontDescription('Cantarell 33')
HEADER_LIGHT_FONT.set_weight(Pango.Weight.LIGHT)

DAY_FONT = Pango.FontDescription('Cantarell 14')
SELECTED_DAY_FONT = Pango.FontDescription('Cantarell 14')
SELECTED_DAY_FONT.set_weight(Pango.Weight.BOLD)
HIDDEN_DAY_FONT = Pango.FontDescription('Cantarell 14')
HIDDEN_DAY_FONT.set_weight(Pango.Weight.LIGHT)

class CalendarDate:
    day = 0
    str_day = '0'
    hidden = False

    def __str__(self):
        return str(self.day)

# i wish there's some constant that datetime has like this
# it'd be really cool because it can support local shit i think
MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', \
          'July', 'August', 'September', 'October', 'November', 'December']

class CalendarWidget(Widget):
    background_color = (184/255, 61/255, 24/255)

    def __init__(self):
        super().__init__(x=360, width=300, height=300)

        self.now_date = datetime.now()
        self.month = self.elaborate_month(self.now_date)
    
    def draw_widget(self, ctx, layout):
        ctx.set_source_rgba(1, 1, 1, self.alpha)

        # header
        layout.set_font_description(HEADER_LIGHT_FONT)

        ctx.save()
        # _s = 1 + (self.zoom_timer * 0.5)
        # ctx.scale(_s, _s)
        
        # ctx.translate(self.zoom_timer * 110, 0)
        common.context.text(ctx, layout, f"{MONTHS[self.now_date.month-1]} {self.now_date.day}")

        layout.set_font_description(HEADER_FONT)

        str_year = str(self.now_date.year)
        ctx.move_to(self.width-25-common.context.text_bounds(layout, str_year).width-(self.zoom_timer*550), 0)
        ctx.move_to(self.width-25-common.context.text_bounds(layout, str_year).width, 0)
        common.context.text(ctx, layout, str_year)
        ctx.restore()

        # text
        ctx.save()
        _s = 1 + (self.zoom_timer * 1.25)
        ctx.scale(_s, _s)

        ctx.translate(self.zoom_timer * 75, 60 - (self.zoom_timer * 20))
        rect_size = 36 # aspect ratio

        for ind_y, week in enumerate(self.month):
            for ind_x, day in enumerate(week):
                if day.hidden:
                    ctx.set_source_rgba(0.1, 0.1, 0.1, 0.15 * self.alpha)
                elif day.day == self.now_date.day:
                    ctx.set_source_rgba(*self._selected_color, self.alpha)
                else:
                    ctx.set_source_rgba(0.1, 0.1, 0.1, 0.5 * self.alpha)

                ctx.save()
                ctx.translate(ind_x * (rect_size + 5), ind_y * (rect_size + 5))

                common.context.rounded_rectangle(ctx, 0, 0, rect_size, rect_size, 10)
                ctx.fill()
                
                
                if day.hidden:
                    layout.set_font_description(HIDDEN_DAY_FONT)
                    ctx.set_source_rgba(1, 1, 1, 0.5 * self.alpha)
                elif day.day == self.now_date.day:
                    layout.set_font_description(SELECTED_DAY_FONT)
                    ctx.set_source_rgba(1, 1, 1, self.alpha)
                else:
                    layout.set_font_description(DAY_FONT)
                    ctx.set_source_rgba(1, 1, 1, self.alpha)

                ctx.translate((rect_size * 0.5) - (\
                        common.context.text_bounds(layout, day.str_day).width * 0.5), 5)
                common.context.text(ctx, layout, day.str_day)
                ctx.restore()

        ctx.restore()

    _selected_color = (207/255, 87/255, 83/255)

    def elaborate_month(self, timeframe):
        month = calendar.monthcalendar(timeframe.year, timeframe.month)

        # can be worked with modulus?
        prev_month_month = timeframe.month - 1
        next_month_month = timeframe.month + 1
        prev_month_year = timeframe.year
        next_month_year = timeframe.year

        if prev_month_month < 1:
            prev_month_month = 12
            prev_month_year -= 1

        if next_month_month > 12:
            next_month_month = 1
            next_month_year += 1

        prev_month = calendar.monthcalendar(prev_month_year, prev_month_month)
        next_month = calendar.monthcalendar(next_month_year, next_month_month)
        
        for sub_i, sub_month in enumerate(month):
            for i, day in enumerate(sub_month):
                n = CalendarDate()
                n.day = day
                n.str_day = str(n.day)
                
                month[sub_i][i] = n

        for i, (last_week_day, first_week_day) in enumerate(zip(prev_month[-1], month[0])):
            if first_week_day.day > 0:
                continue

            n = CalendarDate()
            n.day = last_week_day
            n.str_day = str(n.day)
            n.hidden = True

            month[0][i] = n
       
        for i, (first_week_day, last_week_day) in enumerate(zip(next_month[0], month[-1])):
            if last_week_day.day > 0:
                continue
            
            n = CalendarDate()
            n.day = first_week_day
            n.str_day = str(n.day)
            n.hidden = True

            month[-1][i] = n
            


        return month
