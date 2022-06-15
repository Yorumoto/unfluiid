import os
from posixpath import splitext


class Entry:
    def __init__(self, path):
        self.path = path

    def parse(self):
        data = ''

        with open("test.desktop", 'r') as f:
            data = f.read()

        ## first extract lines from data
        # and remove comments
        
        ## parse each [] header, could be main or action
        # inside here there are keys and values
        
        # profit

    def can_show(self):
        pass

if __name__ == '__main__':
    desktop_directory = '/usr/share/applications'

    for path in os.listdir(desktop_directory):
        full_path = os.path.join(desktop_directory, path)

        _, ext = os.path.splitext(path)
        
        if ext != ".desktop":
            continue

        print(f'parsing {full_path}...')
        entry = Entry(full_path)
        entry.parse()

        break
