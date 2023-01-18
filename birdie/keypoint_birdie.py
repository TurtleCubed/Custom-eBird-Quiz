from cub import Cub
import matplotlib.pyplot as plt
import numpy as np
import random

a = Cub("./birdie/CUB_200_2011", as_pts=True)
for i in random.sample(range(len(a)), len(a)):
    bird = a[i]
    img = bird["image"]
    part_locs = bird["part_locs"]
    part_ids = bird["part_ids"]
    bbox = bird["bbox"]
    impt = a._parts_importance
    colors = {0:"red", 1:"yellow", 2:"green", 3:"blue", 4:"purple", 5:"black"}
    plt.imshow(img)
    plt.scatter(part_locs[:, 0], part_locs[:, 1], c=[colors[impt[part_ids[i]]] for i in range(len(part_ids))])
    plt.scatter([bbox[0], bbox[0], bbox[0] + bbox[2], bbox[0] + bbox[2]], [bbox[1], bbox[1] + bbox[3], bbox[1], bbox[1] + bbox[3]], c="brown")
    plt.show()
