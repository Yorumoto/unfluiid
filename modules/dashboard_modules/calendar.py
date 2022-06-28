import calendar
from datetime import date, datetime

from modules.dashboard_modules.util import Widget

class CalendarDate:
    day = 0
    str_day = '0'
    hidden = False

    def __str__(self):
        return str(self.day)


class CalendarWidget(Widget):
    def __init__(self):
        super().__init__()

        self.month = self.elaborate_month(datetime.now())
        print([[str(d) for d in x] for x in self.month])

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
