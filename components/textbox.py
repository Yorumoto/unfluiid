from gi.repository import Gdk

ascii_range = range(31, 127)

class Textbox:
    def __init__(self):
        self.input = ""
        self.cursor_position = 0

        self.home_end_enabled = True

    def get_bounds(self, view_side=20):
        offset = (self.cursor_position // view_side) * view_side
        return (offset, offset + view_side), self.cursor_position - offset

    def controlled(self, event):
        return bool(event.state & Gdk.ModifierType.CONTROL_MASK)

    def handle_event(self, event, controlled=None):
        if controlled is None:
            controlled = self.controlled(event) 

        if event.hardware_keycode == 110 and self.home_end_enabled:
            self.cursor_position = 0
        elif event.hardware_keycode == 115 and self.home_end_enabled:
            self.cursor_position = len(self.input)
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

        elif event.hardware_keycode == 119:
            self.input = self.input[0:self.cursor_position] \
                    + self.input[self.cursor_position+1:]
        elif event.hardware_keycode == 22 and self.cursor_position > 0:
            self.input = self.input[0:self.cursor_position-1] \
                    + self.input[self.cursor_position:]

            self.cursor_position = min(self.cursor_position - 1, len(self.input))
        elif event.keyval in ascii_range:
            at_last = self.cursor_position == len(self.input)

            if at_last:
                self.input += chr(event.keyval)
                self.cursor_position = len(self.input)
            else:
                self.input = self.input[0:self.cursor_position] \
                        + chr(event.keyval) + self.input[self.cursor_position:]

                self.cursor_position += 1