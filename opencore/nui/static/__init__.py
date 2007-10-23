import os

def render_static(fname):
    curdir = os.path.dirname(__file__)
    filename = os.path.join(curdir, fname)
    file_obj = file(filename)
    data = file_obj.read()
    file_obj.close()
    return data
