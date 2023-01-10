import os

def explode(dir):
    for root, dirs, files in os.walk(dir):
        if root != dir:
            for name in files:
                new_name = root[len(dir) + 1:] + "--" + name
                os.rename(os.path.join(root, name), os.path.join(dir, new_name))
            os.rmdir(root)

explode(os.getcwd())
