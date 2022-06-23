from gi.repository import Gdk

ascii_range = range(31, 127)
keypad_numbers_range = range(6, 16)

keypad_number_offset = 65450

class Textbox:
    def __init__(self):
        self.input = ""
        self.cursor_position = 0
        self.input_disabled = False
        self.home_end_enabled = True

    def get_bounds(self, view_side=20):
        offset = (self.cursor_position // view_side) * view_side
        return (offset, offset + view_side), self.cursor_position - offset

    def in_ascii_range(self, event_val):
        return event_val in ascii_range
    
    def in_keyboard_numbers(self, event_val):
        return event_val in keypad_numbers_range

    def num_lock(self, event):
        return bool(event.state & Gdk.ModifierType.MOD2_MASK)

    def modded(self, event):
        return bool(event.state & Gdk.ModifierType.MOD1_MASK)

    def controlled(self, event):
        return bool(event.state & Gdk.ModifierType.CONTROL_MASK)

    def insert(self, char):
        at_last = self.cursor_position == len(self.input)

        if at_last:
            self.input += char
            self.cursor_position = len(self.input)
        else:
            self.input = self.input[0:self.cursor_position] \
                    + char + self.input[self.cursor_position:]

            self.cursor_position += 1


    def handle_event(self, event, controlled=None):
        if controlled is None:
            controlled = self.controlled(event)
        
        c = False # changed
        
        if self.input_disabled:
            return c

        if event.hardware_keycode == 110 and self.home_end_enabled:
            self.cursor_position = 0
            c = True
        elif event.hardware_keycode == 115 and self.home_end_enabled:
            self.cursor_position = len(self.input)
            c = True
        elif event.hardware_keycode in [113, 114]:
            inc = -1 if event.hardware_keycode == 113 else 1

            if controlled:
                old = self.cursor_position
                partition = (" " + self.input[0:self.cursor_position-1]) \
                        if inc <= 0 else (self.input[self.cursor_position:] + " ")

                if inc > 0:
                    position = partition.find(" ", 1)
 
                    if position > 0:
                        self.cursor_position = position + old
                    elif partition == self.input:
                        self.cursor_position = len(self.input)
                elif self.cursor_position > 0:
                    self.cursor_position = max(partition.rfind(" ", 1), 0)
            else:
                self.cursor_position = min(max(self.cursor_position + inc, 0), \
                        len(self.input))
            
            c = True
        elif (event.hardware_keycode in [22, 25]) and controlled:
            oldlen = len(self.input)

            left = self.input[0:self.cursor_position]
            right = self.input[self.cursor_position:] 
            new_left = left.rsplit(' ', 1)[0]

            if new_left == left:
                self.input = right
            else:
                self.input = new_left + right

            self.cursor_position += len(self.input) - oldlen
            c = True
        elif event.hardware_keycode == 119:
            self.input = self.input[0:self.cursor_position] \
                    + self.input[self.cursor_position+1:]
            
            c = True
        elif event.hardware_keycode == 22 and self.cursor_position > 0:
            self.input = self.input[0:self.cursor_position-1] \
                    + self.input[self.cursor_position:]

            self.cursor_position = min(self.cursor_position - 1, len(self.input))
            
            c = True
        elif self.in_ascii_range(event.keyval):
            self.insert(chr(event.keyval))
            c = True
        # keypad support?
        elif self.num_lock(event) and self.in_keyboard_numbers(event.keyval - keypad_number_offset):
            self.insert(str(event.keyval - keypad_number_offset - 6))
            c = True

        return c
