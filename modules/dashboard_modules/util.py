from time import perf_counter as get_time
import common.context

def mouse_hovering(device_position, x, y, width, height):
    # device_position = window.pointer_device.get_position()

    return device_position.x > x and device_position.x < x + width and \
            device_position.y > y and device_position.y < y + height

class Widget:
    background_color = (1, 1, 1)

    def __init__(self, x=0, y=0, width=200, height=200):
        self.start_x = x
        self.start_y = y
        self.start_width = width
        self.start_height = height

        self.x = self.start_x
        self.y = self.start_y
        self.width = self.start_width
        self.height = self.start_height
        self.padding = 10

        # TODO: integrate custom widgets with these
        self.draw_x = self.x
        self.draw_y = self.y
        self.draw_inner_x = self.x + self.padding
        self.draw_inner_y = self.y + self.padding
        self.draw_width = self.width
        self.draw_height = self.height

        self.wobble_timer = 0
        self.alpha = 1
        self.press_time = 0

        self.colliding = False
        self.holding = False

    def on_press(self, press_time):
        self.holding = self.colliding

    def on_release(self):
        self.holding = False

    def on_click(self, press_release_time):
        pass

    def update_widget(self, dt):
        pass

    def update(self, dt, global_alpha):
        self.alpha = global_alpha

        if self.holding:
            self.holding = self.colliding

        self.update_widget(dt)

    def draw_widget(self, ctx):
        pass

    def draw(self, ctx, layout):
        ctx.set_source_rgba(*self.background_color, self.alpha)
        common.context.rounded_rectangle(ctx, self.x, self.y, self.width, self.height)
        ctx.fill()
        
        ctx.save()
        ctx.translate(self.x + self.padding, self.y + self.padding)
        self.draw_widget(ctx, layout)
        ctx.restore()
