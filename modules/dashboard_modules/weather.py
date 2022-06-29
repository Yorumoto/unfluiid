from threading import Thread

import requests
from requests.exceptions import Timeout
from requests.models import HTTPError

from modules.dashboard_modules.util import Widget
from modules.dashboard_modules.weather_constants import WeatherCodeDatabase

import time
import cairo
import common.context
from common.context import _DPI
from gi.repository import Pango

LINK = "https://wttr.in/?format=j1"

LARGE_HEADER_FONT = Pango.FontDescription('Cantarell 30')

class Temprature:
    celsius = 0
    fahrenheit = 0

class WeatherData:
    weather_code = 0
    temprature = None

class WeatherWidget(Widget):
    background_color = (161/255, 81/255, 70/255)


    def load_weather_data(self):
        try:
            data = requests.get(LINK).json()
            current_condition = data['current_condition'][0]

            new_temp = Temprature()
            new_temp.fahrenheit = int(current_condition['temp_F'])
            new_temp.celsius = int(current_condition['temp_C'])

            self.weather_data = WeatherData()
            self.weather_data.weather_code = int(current_condition['weatherCode'])
            self.weather_data.info = WeatherCodeDatabase.get(self.weather_data.weather_code)
            self.weather_data.temprature = new_temp
            self.loaded = True
        except (ConnectionError, HTTPError, Timeout, KeyError) as e:
            print(f'failed to get weather data: {e}')

    def __init__(self):
        super().__init__(y=305, width=350, height=275)
        
        self.weather_data = None
        self.loaded = False
        self._lt = 0
        self._r = 0

        t = Thread(target=self.load_weather_data)
        t.daemon = True
        t.start()
    
    def update_widget(self, dt):
        self._r += 10 * dt
        self._lt = min(self._lt + (dt * self.loaded * 5), 1)

    def draw_widget(self, ctx, layout):
        ctx.set_source_rgba(1, 1, 1, self.alpha)
       
        rev_lt = 1 - self._lt

        if self.weather_data is not None and self._lt > 0:
            ctx.save()
            layout.set_font_description(LARGE_HEADER_FONT)
            ctx.set_source_rgba(1, 1, 1, self.alpha * self._lt)
            ctx.save()
            ctx.scale(3, 3)
            common.context.text(ctx, layout, self.weather_data.info.icon)
            ctx.restore()
            ctx.restore()

        if self._lt < 1:
            ctx.save()
            ctx.set_source_rgba(0.2, 0.2, 0.2, (self.alpha * 0.6) * rev_lt) 
            common.context.rounded_rectangle(ctx, (self.width * 0.5) - 50 - self.padding, (self.height * 0.5) - 50 - self.padding, 100, 100, 10)
            ctx.fill()
            ctx.set_line_width(10)
            ctx.set_line_cap(cairo.LineCap.ROUND)
            ctx.set_source_rgba(1, 1, 1, self.alpha * rev_lt)
            ctx.arc(self.width * 0.5 - self.padding, self.height * 0.5 - self.padding, 30, self._r - .25, self._r + (_DPI * 0.455 - 0.25))
            ctx.stroke()
            ctx.restore() 
