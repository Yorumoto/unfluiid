from gi.repository import GLib, Gtk
from time import perf_counter as get_time

class Looper:
    _lt = 0

    def __init__(self):
        self._lt = get_time()

    def update(self, dt):
        pass

    def _first_update(self):
        self.update(get_time() - self._lt)
        self._lt = get_time()
        return True

    def loop_init(self, call_gtk_main=True):
        self._lt = get_time()
        self.callback_number = GLib.timeout_add(5, self._first_update)

        if call_gtk_main:
            Gtk.main()
