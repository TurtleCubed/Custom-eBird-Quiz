from checklist import BirdAPI
from map import GMap
from math import exp

REGION = "United States"
N_GAMES = 2

# TODO fetch all checklists in advance
# TODO show locations guessed and stuff like that (end of game screen)
# TODO show checklist comments for the lols
# TODO make api key secret
# TODO different zooms? z17 or z15?
# TODO multiplayer?

regions = {
    "California": "US-CA",
    "Santa Clara County": "US-CA-085",
    "United States": "US"
}
views = {
    "California": "37.1842967,-123.7977755,6z",
    "Santa Clara County": "37.2066118,-121.8113602,9.78z",
    "United States": "40.094099,-98.3882497,4z"
}
scores = {
    "California": 143.2,
    "Santa Clara County": 8.58,
    "United States": 508.7
}

def score(d):
    return 5000 * exp(-d/scores[REGION])

def play_game(n_games):
    a = BirdAPI(regions[REGION])
    g = None
    s = []
    for i in range(n_games):
        a.new_checklist()
        print(a.get_checklist(), end="")
        lon, lat, name = a.get_location()

        if g is None:
            g = GMap(views[REGION])

        guess = g.wait_click_pin()
        g.show_true(guess, (lon, lat))
        print(name)
        dist = g.distance(guess, (lon, lat))
        s.append(score(dist))
        print(f"{s[-1]:0.0f} points. Your guess was off by distance {g.distance(guess, (lon, lat)):.2f} km")
        if i+1 == n_games or input(f"Continue game? You just finished round {i+1} out of {n_games} (Y/n): ") == "n":
            break
        g.reset()
    input(f"Your total score was {sum(s):0.0f}/{5000 * (i+1)}. Press enter to exit the game.")
    g.close()

play_game(N_GAMES)