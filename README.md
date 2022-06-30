# unfluiid
*version 1 :)*

![insert image here]()

A rice where I reinvented the wheel (polybar, bar, eww, rofi, dunst, and maybe awesome) just for cool transitions. 

The code is mid messy, so forking will be a pain in the ass, so it's rather a showcase than something for a template to begin with. (It's better that I'll probably drop an API to make rices almost in Python or move to AwesomeWM)

## Installation
You'll need an i3wm/sway desktop environment, because it uses the i3ipc dependency for displaying the window titles and workspaces.

1. Install some fonts.
- [Iosevka Term Nerd Font Complete Mono](https://github.com/ryanoasis/nerd-fonts/blob/master/patched-fonts/Iosevka/Regular/complete/Iosevka%20Term%20Nerd%20Font%20Complete%20Mono.ttf)

2. Install some dependencies for some pip packages (some names will be different depending on your distro; in this case, below will be Arch Linux)
```
gtk3 portaudio
```

2. Install some pip packages
```
i3ipc python-xlib pygi pycairo pydbus sounddevice
```

Each package's usage:
- **i3ipc** | used for workspaces and window titles
- **python-xlib** | some x11 magic possible (for making windows floating top tier like rofi and eww dashboard)
- **pygi** | gobject bindings for python
- **pycairo** | rendering the rice
- **pydbus** | suspend/sleeping events

2. In your window manager's configs, bind those keybinds to launch unfluiid with the following options:
- bar
- search
- dashboard
- powermenu
- screenflash (suitable for letting your desktop go on an suspended state)

Example:
`.../unfluiid bar`

### Known Issues
- The window title seems to overlap when on a screen resolution apparently smaller than 1920x1080, especially if you have many workspaces open.

- The workspaces section seems to freeze after an i3 configuration reload

- Search application requires the i3-sensible-terminal for lazy terminal application launching. For now, install the application from somewhere.

- Positioning issue when unicode characters are shown. (Can be done in the window title by just going to a website with CJK characters on the title)
