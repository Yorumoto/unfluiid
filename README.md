# unfluiid
*version 1 :)*

![insert image here]()

A rice where I reinvented the wheel (polybar, bar, eww, rofi, dunst, and maybe awesome) just for cool transitions. For the exception of the tray which is made in Polybar, I don't know how someone can integrate an entire tray to their UI.

Some of bad programming has been made (my first rice not to mostly depend on configuration scripting)~~, so if you are a coding nazi, spot 'em all!~~


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
