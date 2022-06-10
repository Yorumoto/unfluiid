# i gave up lol

from json import decoder
from json.decoder import JSONDecodeError
from components.looper import Looper
from components.window import Window, WindowType
from components.animator import Animator

from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
from threading import Thread

import os
import cairo

import base64
import json
import subprocess
import common.context

import pytweening


class NotificationData:
    text = None
    header = ""
    icon = None

class NotificationBubble:
    def __init__(self):
        self._at = 0 # appearance timer
        self.notification_data = None

    def update(self, dt):
        self._at = min(self._at + dt * 1.35, 1)

    def draw(self, ctx, window_width, bubble_width, y, main_program): # last argument is kinda dumb
        ctx.save()
        
        _at_quad = max(pytweening.easeInOutQuint(self._at), 0.005)
        ctx.translate(window_width - (bubble_width * _at_quad), y)

        ctx.scale(_at_quad, _at_quad)

        ### drawing!

        ctx.set_source_rgba(0.225, 0.2, 0.225, 0.8 * _at_quad)
        
        header_height = 50
        body_height = 0

        common.context.rounded_rectangle(ctx, 0, 0, bubble_width, header_height + body_height, 10)
        ctx.fill()
        
        ctx.set_source_rgba(1, 1, 1, 1 * _at_quad)

        ctx.translate(10, 0)
        ctx.save()
        
        # yea i think it's VERY dumb to connect one class to another 
        # like a mother-child relationship

        # TODO: draw parsed text
        

        ctx.restore()
        

        ####

        ctx.restore()

        return (header_height + body_height + 2) * _at_quad

class Main(Looper):
    _new_size_x = 300
    _new_size_offset = 0

    def __init__(self):
        super().__init__()
       
        self.notification_bubbles = []

        self.notification_process = subprocess.Popen(['executables/tiramisu', '--json'], stdout=subprocess.PIPE)
        self.notification_reciever_thread = Thread(target=self.recieve_notifications)
        self.notification_reciever_thread.daemon = True
        self.notification_reciever_thread.start()

        self.window = Window(WindowType.Floating)

        self.pango_layout = None
        
        self._setup = False

        # should use some sort of font name library function fallback in case someone
        # decides to remove cantarell or has another main default font


        self.main_animator = Animator(self.window)
        self.main_animator.main_draw_callback = self.draw
        self.window.connect_animated_overlay(self.main_animator)

        self.window.create_window()
        
        monitor = self.window.screen.get_monitor_geometry(self.window.screen.get_monitor_at_window(self.window.toplevel))
        
        self.window_hidden = False

        self.window.move(monitor.width - self._new_size_x - self._new_size_offset - 10, 10 + self.window._bar_size)
        self.window.show_all()
        
        self.update_height = 300 
        
        self.loop_init()

    
    def notify(self, body):
        notification_data = NotificationData()
        notification_data.header = body.get('summary') 
        notification_data.text = body.get('body') if body.get('body') else None

        hints = body.get('hints')

        if 'image-data' in hints:
            width, height, stride, is_alpha, sample, channels, image_data = tuple(hints.get('image-data').split(':'))
            width = int(width)
            height = int(height)
            stride = int(stride)
            sample = int(sample)
            channels = int(channels)
            is_alpha = is_alpha == "true"
            image_data = GLib.Bytes(base64.decodebytes(bytes(image_data, 'utf-8')))        

            notification_data.icon = GdkPixbuf.Pixbuf.new_from_bytes(image_data, GdkPixbuf.Colorspace.RGB, is_alpha, sample, width, height, stride)

        notification_bubble = NotificationBubble()
        notification_bubble.notification_data = notification_data

        self.notification_bubbles.insert(0, notification_bubble)

    def recieve_notifications(self):
        completed_c = ""

        for c in iter(self.notification_process.stdout.readline, b""):
            completed_c += c.decode()

            try:
                if completed_c[0] != "{" or completed_c[len(completed_c)-2] != "}":
                    continue
                
                self.notify(json.loads(completed_c, strict=False))
                completed_c = ""
            except json.decoder.JSONDecodeError as e:
                # for i, char in enumerate(completed_c[61:100]):
                #    print(i, ord(char), char)

                print(e)
                pass

        Gtk.main_quit()

            # f.write(c)
        
    def draw(self, ctx, width, height):
        y = 0
        
        # ctx.set_source_rgba(1, 1, 1, 1)
        # ctx.rectangle(0, 0, width, height)
        # ctx.fill()

        for bubble in self.notification_bubbles:
            a = bubble.draw(ctx, width, self._new_size_x, y, self)
            y += a

        self.update_height = y

    def update(self, dt):
        self.window.resize(self._new_size_x + self._new_size_offset, max(int(self.update_height), 1))

        for bubble in self.notification_bubbles:
            bubble.update(dt)

        if not self.window_hidden:
            self.main_animator.draw()

