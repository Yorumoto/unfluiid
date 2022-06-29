from threading import Thread

import requests
from requests.exceptions import Timeout
from requests.models import HTTPError

from modules.dashboard_modules.util import Widget
import time

LINK = "https://wttr.in/?format=j1"

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
            self.weather_data.temprature = new_temp 
        except (ConnectionError, HTTPError, Timeout, KeyError) as e:
            print(f'failed to get weather data: {e}')

    def __init__(self):
        super().__init__(y=305, width=300, height=275)
        
        self.weather_data = None
        self.loaded = False
        self._lt = 0

        t = Thread(target=self.load_weather_data)
        t.daemon = True
        t.start()

    def draw_widget(self, ctx, layout):
        ctx.set_source_rgba(1, 1, 1, self.alpha)



