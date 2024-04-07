import numpy as np

EASY = [
    "Pine Warbler",
    "Common Yellowthroat",
    "Yellow-rumped Warbler",
    "Yellow Warbler",
    "Ovenbird",
    "Black-and-white Warbler",
    "American Redstart",
    "Black-throated Green Warbler",
    "Chestnut-sided Warbler",
    "Palm Warbler",
    "Northern Parula",
    "Black-throated Blue Warbler"
]

MEDIUM = [
    "Blue-winged Warbler",
    "Magnolia Warbler",
    "Louisiana Waterthrush",
    "Blackburnian Warbler",
    "Northern Waterthrush",
    "Prairie Warbler",
    "Nashville Warbler",
    "Blackpoll Warbler",
    "Canada Warbler"
]

HARD = [
    "Worm-eating Warbler",
    "Cerulean Warbler",
    "Tennessee Warbler",
    "Wilson's Warbler",
    "Bay-breasted Warbler",
    "Cape May Warbler"
]

EXTREME = [
    "Mourning Warbler",
    "Golden-winged x Blue-winged Warbler",
    "Hooded Warbler"
]

IMPOSSIBLE = [
    "Orange-crowned Warbler",
    "Kentucky Warbler",
    "Golden-winged Warbler",
    "Prothonotary Warbler",
    "Connecticut Warbler",
    "MacGillivray's Warbler",
    "Yellow-throated Warbler",
    "Townsend's Warbler",
    "Hermit Warbler"
]

values = [EASY, MEDIUM, HARD, EXTREME, ["Any Impossible Warbler"]]

def easy_win(cats, transpose=False):
    # Returns True if any win has sum <= 4 or (either no extreme/impossible or <2 hard)

    # Check if there is a extreme/impossible in every win
    extremes = (cats >= 3)
    if np.any(np.logical_not(np.any(extremes, axis=1))):
        # For lines without extreme/impossible, check for at least 2 hards, no more than 1 easy
        if np.any(np.sum((cats == 2)[np.logical_not(np.any(extremes, axis=1))], axis=1) < 2) or np.any(np.sum((cats == 0)[np.logical_not(np.any(extremes, axis=1))], axis=1) > 1):
            return True
    # Check if there is sum <= 4
    if np.any(np.sum(cats, axis=0) <= 4):
        return True
    # Check diagonal sum
    if not transpose and np.trace(cats) <= 4:
        return True
    elif transpose and np.trace(np.fliplr(cats)) <= 4:
        return True
    
    if transpose:
        return False
    else:
        return False or easy_win(cats.T, True)

def min_sum(cats):
    return np.min((np.min(np.sum(cats, axis=0)), np.min(np.sum(cats, axis=1)), np.trace(cats), np.trace(cats.T)))

def valid_hist(cats):
    dist = np.histogram(cats, 5, range=(0, 4))[0]
    return not np.any(dist > np.array([len(x) for x in values]))
    

def get_bingo():
    while True:
        cats = np.random.randint(0, 3, size=(5, 5))
        cats[2, 2] = 4 # Center = impossible
        extreme_pos = np.random.randint(0, 5, size=(3, 2))
        cats[extreme_pos[:, 0], extreme_pos[:, 1]] = 3
        if np.sum(cats == 3) == 3 and valid_hist(cats) and not easy_win(cats) and min_sum(cats) < 6:
            # print(min_sum(cats))
            break
    dist = np.histogram(cats, 5, range=(0, 4))[0]
    bingo_vals = [list(np.random.choice(values[i], size=dist[i], replace=False)) for i in range(len(dist))]
    bingo_out = cats.copy().flatten().astype("object")
    for i in range(len(bingo_out)):
        bingo_out[i] = bingo_vals[bingo_out[i]].pop()
        print(bingo_out[i], end="\n" if i % 5 == 4 else ";")

for _ in range(20):
    get_bingo()
    print()