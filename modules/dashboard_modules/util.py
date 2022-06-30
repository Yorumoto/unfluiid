from time import perf_counter as get_time
import common.context

from random import choice

RAND_OFFSETS = [(-1, 0), (1, 0), (0, 1), (0, -1)]

def mouse_hovering(device_position, x, y, width, height):
    # device_position = window.pointer_device.get_position()

    return device_position.x > x and device_position.x < x + width and \
            device_position.y > y and device_position.y < y + height

class Widget:
    background_color = (1, 1, 1)

    def __init__(self, x=0, y=0, width=200, height=200):
        self.main_widget = None

        self.start_x = x
        self.start_y = y
        self.start_width = width
        self.start_height = height
        
        offset_choice = choice(RAND_OFFSETS)
        self.origin_offset_x = offset_choice[0] * 300
        self.origin_offset_y = offset_choice[1] * 300

        self.x = self.start_x
        self.y = self.start_y
        self.width = self.start_width
        self.height = self.start_height
        self.padding = 12
        # self.inner_padding = 0

        self.no_zoom = False
        self.zoom_timer = 0
        self._zt = 0 # linear zoom timer
        
        self.appearance_timer = 0
        self._at = 0 # linear appearance timer
        self.appearance_del_timer = 0

        self.alpha = 1
        
        self.colliding = False
        self.holding = False
        self.hold_since = 0

    def on_quit(self):
        pass

    def on_press(self, press_time):
        self.hold_since = press_time
        self.holding = self.colliding and not self.no_zoom

    def on_release(self):
        self.holding = False

    def on_click(self, press_release_time):
        pass

    def update_widget(self, dt):
        pass

    def update(self, dt, global_alpha):
        self.alpha = self.appearance_timer * global_alpha

        if self.holding:
            self.holding = self.colliding

        self.update_widget(dt)

    def draw_widget(self, ctx, layout):
        pass

    def draw_background(self, ctx):
        ctx.set_source_rgba(*self.background_color, self.alpha)
        common.context.rounded_rectangle(ctx, self.x, self.y, self.width, self.height)
        ctx.fill()

    def draw(self, ctx, layout):
        self.draw_background(ctx)
        
        ctx.save()
        ctx.translate(self.x + self.padding, self.y + self.padding)
        self.draw_widget(ctx, layout)
        ctx.restore()
