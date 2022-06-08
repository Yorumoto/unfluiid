#!/usr/bin/python3

import gi
gi.require_version('Gtk', '3.0')
import sys

import modules.bar

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
    elif mode == 'powermenu':
        pass
    else:
        raise SystemExit('Unknown mode')

try:
    (lambda: __name__ == '__main__' and main())()
except KeyboardInterrupt:
    pass
