import pytweening

class DeltaTween:
    def __init__(self, target=1, start=0, tween_style=pytweening.easeInOutQuad):
        self._c = start # current
        self._d = 1 # difference
        self._t = 0 # time (0-1)
        self._s = start # start
        self._i = False # inited
 
        if start != target:
            self.change_target(target)

        self.tween_style = tween_style

    def change_target(self, target):
        self._t = 0
        self._s = self._c
        self._d = target - self._s
        self._i = True

    def update(self, delta):
        if not self._i:
            return

        self._t = max(min(self._t + delta, 1), 0)
        self._c = self._s + (self.tween_style(self._t) * self._d)

    def current(self):
        return self._c
