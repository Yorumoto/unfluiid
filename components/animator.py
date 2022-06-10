from gi.repository import Gtk

class Animator(Gtk.DrawingArea):
    def __init__(self, window):
        super().__init__()
        
        self.connect('draw', self._pre_draw)
        self.window = window
        self.connected_to_window = True
        
        self.main_draw_callback = None

    def main_draw(*_):
        pass

    def draw(self):
        self.queue_draw()

    def _pre_draw(self, widget, context):
        if self.connected_to_window:
            window_size = self.window.get_size()
            self.set_size_request(window_size.width, window_size.height)

        # context.set_source_rgba(1.0, 1.0, 1.0, 0.2)
        (self.main_draw_callback or self.main_draw)(context, self.get_allocated_width(), self.get_allocated_height() - (self.window.get_border_width() * 2))
