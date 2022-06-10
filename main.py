#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
import sys

import modules.bar
import modules.screenflash
import modules.notification

def main():
    if len(sys.argv) <= 1:
        raise SystemExit('Mode not specified')

    mode = sys.argv[1]
    
    if mode == 'bar':
        modules.bar.Main()
    elif mode == 'dashboard':
        pass
    elif mode == 'search':
        pass
    # elif mode == "notification":
    #    modules.notification.Main()
    # pango lol
    elif mode == 'powermenu':
        pass
    elif mode == "screenflash":
        modules.screenflash.Main()
    else:
        raise SystemExit('Unknown mode')

try:
    (lambda: __name__ == '__main__' and main())()
except KeyboardInterrupt:
    pass
