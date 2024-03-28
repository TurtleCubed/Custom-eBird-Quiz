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
    "Northern Parula"
]

MEDIUM = [
    "Palm Warbler",
    "Blue-winged Warbler",
    "Magnolia Warbler",
    "Louisiana Waterthrush",
    "Blackburnian Warbler",
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
    "Cape May Warbler",
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

values = [EASY, MEDIUM, HARD, ["Any Impossible Warbler"]]

def easy_win(cats):
    # Returns True if any win has sum <= 3 or no hard/impossible birds
    for ax in range(2):
        # Check if there is a hard/impossible in every win
        hard = (cats >= 2)
        if np.any(np.logical_not(np.any(hard, axis=ax))):
            return True
        # Check if there is sum < 4
        if np.any(np.sum(cats, axis=ax) <= 3):
            return True
    # Check diagonal sums
    if np.trace(cats) <= 3 or np.trace(cats.T) <= 3:
        return True
    return False

def min_sum(cats):
    return np.min((np.min(np.sum(cats, axis=0)), np.min(np.sum(cats, axis=1)), np.trace(cats), np.trace(cats.T)))

def valid_hist(cats):
    dist = np.histogram(cats, 4)[0]
    return not np.any(dist > np.array([len(x) for x in values]))
    

def get_bingo():
    while True:
        cats = np.random.randint(0, 3, size=(5, 5))
        cats[2, 2] = 3
        if not easy_win(cats) and min_sum(cats) < 6 and valid_hist(cats):
            # print(min_sum(cats))
            break

    dist = np.histogram(cats, 4)[0]
    bingo_vals = [list(np.random.choice(values[i], size=dist[i], replace=False)) for i in range(len(dist))]
    bingo_out = cats.copy().flatten().astype("object")
    for i in range(len(bingo_out)):
        bingo_out[i] = bingo_vals[bingo_out[i]].pop()
        print(bingo_out[i], end="\n" if i % 5 == 4 else ";")

for _ in range(20):
    get_bingo()
    print()