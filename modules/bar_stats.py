import common.context
import time
import psutil
import netifaces
import pytweening

import alsaaudio

class Bar:
    _bar_width = 150
    _default_bar_width = 150

    def __init__(self):
        self._x = None
        self._h = None

    def draw(self, ctx, x, height):
        self._x = x - self._bar_width
        self._h = height

        ctx.set_source_rgba(0.2, 0.1, 0.3, 0.75)
        common.context.rounded_rectangle(ctx, self._x, 0, self._bar_width, height, height * 0.5)
        ctx.fill()

        ctx.save()
        ctx.translate(self._x, 0)
        
        new_width = self.main_draw(ctx, height, self._bar_width)
        
        if new_width is not None:
            self._bar_width = max(self._default_bar_width, new_width)

        ctx.restore()

        return self._bar_width + 10
    
    def collides(self, cx, cy):
        if self._x is None:
            return False

        # a poor way to layout the bars, could've just update the layouts in the update field

        return cx > self._x and cx < self._x + self._bar_width and cy > 2 and cy < self._h

    def main_draw(*_):
        pass

class PowerMain(Bar):
    colors = (1, 186/255, 45/255)
    symbol = ""

    def __init__(self, bar):
        super().__init__()

        self._force_view_text = False

        self.bar = bar
        self.percentage_text = "0.0%"
        self.percentage = 0

        self._vtt = 0 # view text time

    def update_stats(self):
        self.percentage = psutil.cpu_percent() / 100
        self.percentage_text = f"{(self.percentage * 100):.1f}%"

    def update(self, dt):
        _, cx, cy = self.bar.pointer_device.get_position()

        self._vtt = max(min(self._vtt + (dt if (self._force_view_text or self.collides(cx, cy)) else -dt) * 5, 1), 0)

    def main_draw(self, ctx, height, width):
        ctx.set_source_rgba(0.4, 0.4, 0.4, 1)

        _vtt = pytweening.easeInOutQuad(self._vtt)
        
        bar_y = ((height * 0.5) - 2.5) + (_vtt * 7)

        max_progress_width = self._bar_width * 0.6
        common.context.rounded_rectangle(ctx, 40, bar_y, max_progress_width, 5, 2)
        ctx.fill()

        ctx.set_source_rgba(*self.colors, _vtt)

        ctx.set_font_size(12)
        ctx.save()
        ctx.translate(40, height * 0.55)
        ctx.show_text(self.percentage_text)
        ctx.restore()

        ctx.set_source_rgba(*self.colors, 1)
        common.context.rounded_rectangle(ctx, 40, bar_y, max_progress_width * self.percentage, 5, 2)
        ctx.fill()

        ctx.set_font_size(int(height * 0.8))
        ctx.save()
        ctx.translate(15, height * 0.8)
        ctx.show_text(self.symbol)
        ctx.restore()


# lazy inheritance xd
class MemoryMain(PowerMain):
    colors = (135/255, 135/255, 1)
    symbol = "" 
   
    def __init__(self, bar):
        super().__init__(bar)
        self.percentage_text = "0.0% 0.0GB"

    def update_stats(self):
        memory = psutil.virtual_memory()
        self.percentage = memory.percent / 100
        self.percentage_text = f"{(self.percentage * 100):.1f}% {((memory.used/1024)/1024)/1024:.1f}GB"


class NetworkMain(Bar):
    main_color = (17/255, 212/255, 17/255)
    disconnected_color = (0.4, 0.4, 0.4)

    color =[17/255, 212/255, 17/255]
    
    def __init__(self):
        self.update_stats(force_disconnected=True)

    def update_stats(self, force_disconnected=False):
        if force_disconnected:
            self.color = self.disconnected_color    
            self.link = "disconnected"
            return 

        for interface in ['enp0s25', 'eth0']:
            try:
                self.link = netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr']
                self.color = self.main_color
                break
            except (KeyError, ValueError):
                pass
        else:
            self.update_stats(force_disconnected=True)


    def main_draw(self, ctx, height, width):
        ctx.set_source_rgba(*self.color, 1) 

        ctx.translate(15, 27) 
        ctx.set_font_size(25)
        ctx.show_text("說")

        ctx.set_font_size(18)
        extents = ctx.text_extents(self.link)

        ctx.move_to(20, -2)

        ctx.show_text(self.link)

        return extents.width + 50

class TimeMain(Bar):
    def __init__(self):
        self.update_stats()

    def update_stats(self):
        self.datetime = time.strftime("%H:%M:%S %m/%d-%w") # time.strftime("%H:%M %m-%d:%w") 

    def main_draw(self, ctx, height, width):
        ctx.set_source_rgba(1, 1, 1, 1) 

        ctx.translate(15, 27) 
        ctx.set_font_size(25)
        ctx.show_text("")

        ctx.set_font_size(18)
        extents = ctx.text_extents(self.datetime)

        ctx.move_to(20, -2)

        ctx.show_text(self.datetime)

        return extents.width + 50

class VolumeMain(PowerMain):
    colors = (3/255, 194/255, 252/255)
    volume_symbol = "墳"
    no_volume_symbol = ""
    muted_symbol = "ﱝ"

    def __init__(self, bar):
        super().__init__(bar)
        self.percentage_text = "0%"
        self.update_stats()

    def update_stats(self):
        m = alsaaudio.Mixer()
        vol = m.getvolume()[0]
        muted = m.getmute()[0] == 1

        self.percentage = min(vol / 100, 1)
        self.percentage_text = f"{vol}%"

        self.symbol = self.muted_symbol if muted else (self.no_volume_symbol if vol <= 0 else self.volume_symbol)
        self._force_view_text = vol > 100

class Main:
    def __init__(self, bar):
        self.update_time = 1
        self.update_volume_time = 0.05

        self.current_update_volume_time = self.update_volume_time
        self.current_update_time = self.update_time

        self.power_main = PowerMain(bar)
        self.memory_main = MemoryMain(bar)
        self.network_main = NetworkMain()
        self.volume_main = VolumeMain(bar)
        self.time_main = TimeMain()
   
    def update(self, dt):
        self.power_main.update(dt)
        self.memory_main.update(dt)
        self.volume_main.update(dt)

        if self.current_update_volume_time <= 0:
            self.volume_main.update_stats()
            self.current_update_volume_time = self.update_volume_time
        else:
            self.current_update_volume_time -= dt

        if self.current_update_time <= 0:
            self.power_main.update_stats()
            self.memory_main.update_stats()
            self.network_main.update_stats()
            self.time_main.update_stats()

            self.current_update_time = self.update_time
        else:
            self.current_update_time -= dt

    def draw(self, ctx, width, height):
        # x = (width - self.time_main._bar_width) - 32
        x = width - 8
        
        x -= self.time_main.draw(ctx, x, height)
        x -= self.network_main.draw(ctx, x, height)
        x -= self.volume_main.draw(ctx, x, height)
        x -= self.memory_main.draw(ctx, x, height)
        x -= self.power_main.draw(ctx, x, height)
