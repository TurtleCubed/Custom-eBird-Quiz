import os

def implode(dir):
    for root, dirs, files in os.walk(dir):
        if root == dir:
            for name in files:
                if len(name.split("--")) > 1:
                    old_dir, old_name = name.split("--")
                    if not os.path.isdir(os.path.join(root, old_dir)):
                        os.mkdir(os.path.join(root, old_dir))
                    print(old_dir, old_name)
                    os.rename(os.path.join(root, name), os.path.join(dir, old_dir, old_name))

implode(os.getcwd())