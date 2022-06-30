class DatabaseItem:
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon


# hopefully this is accurate
MoonCodeDatabase = {
    'New Moon': '',
    'Waxing Crescent': '',
    'First Quarter': '',
    'Waxing Gibbous': ' ',
    'Full Moon': '',
    'Waning Gibbous': '',
    'Last Quarter': '',
    'Waning Crescent': '',
}

WeatherCodeDatabase = {
    113: DatabaseItem('sunny', ''),
    116: DatabaseItem('partly cloudy', ''),
    119: DatabaseItem('cloudy', ''),
    122: DatabaseItem('very cloudy', ''),
    143: DatabaseItem('fog', ''),
    176: DatabaseItem('light showers', ''),
    179: DatabaseItem('light sleet', ''),
    182: 179,
    185: 179,
    200: DatabaseItem('thunderstorm', ''),
    227: DatabaseItem('light snow', ''),
    230: DatabaseItem('heavy snow', ''),
    248: 143,
    260: 143,
    263: 176,
    266: DatabaseItem('light rain', ''),
    281: 179,
    284: 179,
    293: 266,
    296: 266,
    299: DatabaseItem('heavy showers', ''),
    302: DatabaseItem('heavy rain', ''),
    305: 299,
    308: 302,
    311: 179,
    314: 179,
    317: 179,
    320: 179,
    323: 227,
    326: 227,
    329: 230,
    332: 230,
    335: 230,
    338: 230,
    350: 179,
    353: 176,
    356: 299,
    359: 299,
    362: 179,
    365: 179,
    368: 230,
    371: 230,
    374: 179,
    377: 179,
    386: 200,
    389: 200,
    392: DatabaseItem('thunder show', ''),
    395: 230
}

for key, value in WeatherCodeDatabase.items():
    if not isinstance(value, int):
        continue

    WeatherCodeDatabase[key] = WeatherCodeDatabase[value]
