import numpy as np
import sounddevice as sd

from modules.dashboard_modules.util import Widget
import alsaaudio

from gi.repository import Pango
import cairo
import common.context

VOLUME_FONT = Pango.FontDescription('Cantarell 20')

class VisualizerWidget(Widget):
    chunks = 256

    def __init__(self):
        super().__init__(x=365, y=315, width=610, height=265)
       
        self.input_stream = sd.InputStream(blocksize=self.chunks, callback=self.read_callback)
        self.input_stream.start()

        self.blocks = np.zeros(self.chunks, dtype=np.float32)
        self.smooth_blocks = np.zeros(self.chunks, dtype=np.float32)

        self.volume_percentage = 0
        self.update_volume_stats = 0

    def read_callback(self, new_block, _, t, s):
        self.blocks = new_block[:,0] * (300 * (1 + (self.zoom_timer * .5)))

    def update_widget(self, dt):
        if self.update_volume_stats < 0:
            self.volume_percentage = alsaaudio.Mixer().getvolume()[1]
            self.update_volume_stats = 0.1
        else:
            self.update_volume_stats -= dt

        for i, (smooth_point, point) in enumerate(zip(self.smooth_blocks, self.blocks)):
            smooth_point += (point - smooth_point) * (dt * 25)
            self.smooth_blocks[i] = smooth_point

    def draw_widget(self, ctx, layout):
        ctx.set_source_rgba(1, 1, 1, self.alpha)
        layout.set_font_description(VOLUME_FONT)

        ctx.move_to(15, 5)
        
        common.context.text(ctx, layout, f'{self.volume_percentage}%')
        
        ctx.set_line_width(10)
        
        percentage_clamped = min(self.volume_percentage, 150)

        bar_len = percentage_clamped // 10

        for i in range(bar_len):
            x = 15 + (i * 25)
            ctx.move_to(x, 45)
            ctx.line_to(x + 20, 45)
            ctx.stroke()

        if bar_len != percentage_clamped / 10:
            x = 15 + (bar_len * 25)
            ctx.move_to(x, 45)
            ctx.line_to(x + 20 * ((percentage_clamped / 10) - bar_len), 45)
            ctx.stroke()

        ctx.move_to(0, 0)

        ctx.save()
        ctx.translate(-self.padding, 0)

        ctx.set_line_width(3 + (self.zoom_timer * 3))
        ctx.set_line_cap(cairo.LineCap.ROUND)
        
        ctx.rectangle(0, 0, self.width, self.height)
        ctx.clip()

        cy = self.height * 0.5
        l = len(self.blocks)

        ctx.move_to(-5, cy)

        for i, point in enumerate(self.smooth_blocks):
            x = ((i / l) * self.width)
            y = cy + point

            ctx.line_to(x, y)
            ctx.stroke()
            ctx.move_to(x, y)

        ctx.restore()

    def draw_background(self, ctx):
        ctx.save()
        common.context.rounded_rectangle(ctx, self.x, self.y, self.width, self.height)
        # ctx.rectangle(self.x, self.y, self.width, self.height)
       
        cx = self.x + self.width * 0.5
        self.gradient = cairo.LinearGradient(cx, self.y, cx, self.y + self.height)
        self.gradient.add_color_stop_rgba(0, 0.175, 0.175, 0.15, self.alpha)
        self.gradient.add_color_stop_rgba(0.5, 0.135, 0.135, 0.135, self.alpha)
        self.gradient.add_color_stop_rgba(1, 0.193, 0.193, 0.193, self.alpha)

        ctx.set_source(self.gradient)
        ctx.fill()
        ctx.restore()
