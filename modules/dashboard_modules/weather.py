import json
import os
from threading import Thread

import datetime

import requests
from requests.exceptions import Timeout
from requests.models import HTTPError

from modules.dashboard_modules.util import Widget
from modules.dashboard_modules.weather_constants import WeatherCodeDatabase, DatabaseItem, MoonCodeDatabase

import time
import cairo
import common.context

import components.cache as cache_utils

from common.context import _DPI
from gi.repository import Pango

LINK = "https://wttr.in/?format=j1"

LARGE_HEADER_FONT = Pango.FontDescription('Cantarell 20')
LARGE_HEADER_FONT.set_weight(Pango.Weight.BOLD)

LARGE_ICON_FONT = Pango.FontDescription('Cantarell 125')
MOON_ICON_FONT = Pango.FontDescription('Cantarell 50')

SUB_HEADER_FONT = Pango.FontDescription('Cantarell 15')

HORIZON_TIME_FORMAT = "%H:%M"

class Temprature:
    celsius = 0
    fahrenheit = 0

class WeatherData:
    weather_code = 0
    temprature = None

class HorizonTime:
    rise = datetime.time(0)
    set = datetime.time(0)

    @staticmethod
    def parse_strf(strf_time):
        return datetime.datetime.strptime(strf_time, '%I:%M %p').time()

REFRESH_WEATHER_CACHE_DELAY = 60 * 30

class WeatherWidget(Widget):
    background_color = (161/255, 81/255, 70/255)

    def cache_fetch_weather_data(self, filename):
        data = requests.get(LINK).json()
        data['since'] = time.time()
        
        with open(filename, 'w+') as f:
            f.write(json.dumps(data))

        return data

    def load_weather_data(self):
        try:
            filename = cache_utils.path_join('weather_cache.json')

            if not os.path.isfile(filename):
                data = self.cache_fetch_weather_data(filename)
            else:
                data = json.load(open(filename, 'r'))

                if time.time() - data['since'] > REFRESH_WEATHER_CACHE_DELAY:
                    data = self.cache_fetch_weather_data(filename)
            
            horizon_data = data['weather'][0]['astronomy'][0]
            current_condition = data['current_condition'][0]
            
            new_temp = Temprature()
            new_temp.fahrenheit = int(current_condition['temp_F'])
            new_temp.celsius = int(current_condition['temp_C'])
    
            moon_horizon = HorizonTime()
            moon_horizon.rise = HorizonTime.parse_strf(horizon_data['moonrise'])
            moon_horizon.set = HorizonTime.parse_strf(horizon_data['moonset'])

            sun_horizon = HorizonTime()
            sun_horizon.rise = HorizonTime.parse_strf(horizon_data['sunrise'])
            sun_horizon.set = HorizonTime.parse_strf(horizon_data['sunset'])
            
            moon_phase = DatabaseItem(horizon_data['moon_phase'].lower(), 
                    MoonCodeDatabase.get(horizon_data['moon_phase']))

            moon_phase.illumination = int(horizon_data['moon_illumination'])
            
            self.weather_data = WeatherData()
            self.weather_data.weather_code = int(current_condition['weatherCode'])
            self.weather_data.info = WeatherCodeDatabase.get(self.weather_data.weather_code)
            self.weather_data.temprature = new_temp
            self.weather_data.moon_horizon = moon_horizon
            self.weather_data.moon_phase = moon_phase
            self.weather_data.sun_horizon = sun_horizon

            self.loaded = True
        except (ConnectionError, HTTPError, Timeout, KeyError, ValueError) as e:
            print(f'failed to get weather data: {e}')

    def __init__(self):
        super().__init__(y=315, width=350, height=265)
        
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
            
            ctx.set_source_rgba(1, 1, 1, self.alpha * self._lt)
            
            _s = 1 + (self.zoom_timer * 1.5)

            ctx.save()
            layout.set_font_description(LARGE_ICON_FONT)
            
            ctx.translate(10 + (self.zoom_timer * 35), -40 - (self.zoom_timer * 60))
            ctx.scale(_s, _s)
            common.context.text(ctx, layout, self.weather_data.info.icon)

            layout.set_font_description(LARGE_HEADER_FONT)
            
            ctx.translate(100, 60)
            common.context.text(ctx, layout, self.weather_data.info.name)

            layout.set_font_description(SUB_HEADER_FONT)
            temp = self.weather_data.temprature

            ctx.translate(0, 35)
            common.context.text(ctx, layout, \
                    f"  {temp.celsius}°C {temp.fahrenheit}°F ")
            
            sun_horizon = self.weather_data.sun_horizon

            ctx.translate(0, 25)
            common.context.text(ctx, layout, \
                    f" {sun_horizon.rise.strftime(HORIZON_TIME_FORMAT)}   {sun_horizon.set.strftime(HORIZON_TIME_FORMAT)}")

            ctx.restore()
            
            ctx.save()
            layout.set_font_description(LARGE_ICON_FONT)
            
            ctx.translate(10 + (self.zoom_timer * 35), 60 + (self.zoom_timer * 100))

            _sml = (1 - ((self.weather_data.moon_phase.illumination != 0)\
                    * 0.5)) # scale if moon illumination is 1

            ctx.scale(_s, _s)
            ctx.save()
            
            ctx.scale(_sml, _sml)

            if self.weather_data.moon_phase.illumination != 0:
                ctx.translate(40, 120)

            common.context.text(ctx, layout, self.weather_data.moon_phase.icon)
            ctx.restore()

            layout.set_font_description(LARGE_HEADER_FONT)
            
            ctx.translate(100, 60)
            common.context.text(ctx, layout, self.weather_data.moon_phase.name)

            layout.set_font_description(SUB_HEADER_FONT)
            temp = self.weather_data.temprature

            ctx.translate(0, 35)

            moon_horizon = self.weather_data.moon_horizon

            common.context.text(ctx, layout, \
                    f" {moon_horizon.rise.strftime(HORIZON_TIME_FORMAT)}   {moon_horizon.set.strftime(HORIZON_TIME_FORMAT)}")

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
