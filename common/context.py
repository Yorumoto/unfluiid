from math import pi

# import gi
# gi.require_version("PangoCairo", '1.0')
# from gi.repository import PangoCairo

_DEGREES = pi / 180
_DPI = pi * 2

# default_radius = (25, 25, 25, 25)

PANGO_REDUCE = 1024

# context vs ctx, :thinking:

def rounded_rectangle(context, x, y, width, height, radius=25):
    # if isinstance(radius, int):
        # radius = (radius for _ in range(4))
    # elif radius is None:
        # radius = default_radius

    context.new_path()
    context.arc(x + width - radius, y + radius, radius, -90 * _DEGREES, 0 * _DEGREES)
    context.arc(x + width - radius, y + height - radius, radius, 0 * _DEGREES, 90 * _DEGREES)
    context.arc(x + radius, y + height - radius, radius, 90 * _DEGREES, 180 * _DEGREES)
    context.arc(x + radius, y + radius, radius, 180 * _DEGREES, 270 * _DEGREES)
    context.close_path()

def circle(context, x, y, radius):
    context.new_path()
    context.arc(x, y, radius, 0, _DPI)
    context.close_path()
