# unfluiid
*version 1 :)*

![insert image here]()

A rice where I reinvented the wheel (polybar, bar, eww, rofi, dunst, and maybe awesome) just for cool transitions. 

The code is mid messy, so forking it will be a pain in the ass, so it's a learn-as-you-go project. (It's better that I'll probably drop an API to make rices almost in Python)

## Installation
You'll need an i3wm/sway desktop environment, because it uses the i3ipc dependency for displaying the window titles and workspaces.

1. Install some dependencies for PyGObject
```

```

2. Install some pip packages

```
i3ipc python-xlib pygi pycairo pydbus
```

Each package's usage:
- **i3ipc** | used for workspaces and window titles
- **python-xlib** | some x11 magic possible (for making windows floating top tier like rofi)
- **pygi** | gtk and gdk bindings for python
- **pycairo** | rendering the rice
- **pydbus** | suspend/sleeping events

2. In your window manager's configs, ...

### Known Issues
- The window title (in this case with the `...`) seems to overlap when on a screen resolution apparently smaller than 1920x1080, especially if you have many workspaces open.

- The workspaces section seems to freeze after an i3 configuration reload

- Search application requires the i3-sensible-terminal for lazy terminal application launching. For now, install the application from somewhere.
