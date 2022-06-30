import os

CACHE_DIR = os.path.expanduser('~/.cache/ebirika/unfluiid')

if not os.path.isdir(CACHE_DIR):
    os.makedirs(CACHE_DIR)

def path_join(filename):
    return os.path.join(CACHE_DIR, filename)
