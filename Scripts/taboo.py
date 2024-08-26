
with open('taboo.txt', 'r') as f:
    sps = f.readlines()

import random
from time import time

t = time()
count = 0

while time() - t <= 120:
    i = random.randint(0, len(sps) - 1)
    last = input(sps[i])
    if last != "n":
        count += 1

print(count)
