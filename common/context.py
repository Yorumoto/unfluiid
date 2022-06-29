from math import pi

import gi
gi.require_version("PangoCairo", '1.0')
gi.require_version("Pango", '1.0')
from gi.repository import Pango, PangoCairo

_DEGREES = pi / 180
_DPI = pi * 2

# default_radius = (25, 25, 25, 25)

PANGO_REDUCE = Pango.SCALE

# context vs ctx, :thinking:

def set_layout(layout, text, markup):
    if markup:
        layout.set_text("", -1)
        layout.set_markup(text, -1)
    else:
        layout.set_markup("", -1)
        layout.set_text(text, -1)

def text_bounds(layout, text="hello", markup=False):
    set_layout(layout, text, markup)
    return layout.get_pixel_size()

def text(context, layout, text="hello", markup=False):
    set_layout(layout, text, markup)
    PangoCairo.show_layout(context, layout)

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

def rounded_shadow(context, x, y, width, height, radius=25, depth=10, depth_by=20, depth_alpha=0.125, global_alpha=1, width_offset=20, height_offset=20, color=None): 
    # lotta parameters for one shadow
    # i'm gonna be overwhelmed :dizzy_face:

    context.save()

    if color is None:
        color = (0.1, 0.1, 0.1)


    for i in range(depth):
        completion = i / depth
        db = depth_by * completion

        context.set_source_rgba(*color, completion * depth_alpha * global_alpha)
        rounded_rectangle(context, x + (db * 0.5) - (width_offset * 0.5), y + (db * 0.5) - (height_offset * 0.5), width - db + width_offset, height - db + height_offset, radius)
        context.fill()

    context.restore()

def circle(context, x, y, radius):
    context.new_path()
    context.arc(x, y, radius, 0, _DPI)
    context.close_path()
