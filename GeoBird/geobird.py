from checklist import BirdAPI
from map import GMap
from math import exp
import json

REGION = "Hampshire County"
N_GAMES = 5
LOAD_GAME = None 

# TODO show locations guessed and stuff like that (end of game screen)
# TODO make api key secret
# TODO change pin check from 15/17z to real check
# TODO different browsers?

regions = {
    "California": "US-CA",
    "Santa Clara County": "US-CA-085",
    "United States": "US",
    "Massachusetts": "US-MA",
    "Hampshire County": "US-MA-015",
    "Bristol County": "US-MA-005"
}
views = {
    "California": "37.1842967,-123.7977755,6z",
    "Santa Clara County": "37.2066118,-121.8113602,9.78z",
    "United States": "40.094099,-98.3882497,4z",
    "Massachusetts": "42.0314663,-72.8046168,8z",
    "Hampshire County": "42.3693724,-72.9160787,10z",
    "Bristol County": "41.7557937,-71.3472465,10z"
}
scores = {
    "California": 143.2,
    "Santa Clara County": 8.58,
    "United States": 832.8,
    "Massachusetts": 36.4792,
    "Hampshire County": 8,
    "Bristol County": 8.26684
}

gameinfo = {
    "Region": REGION,
    "Checklists": [],
    "Guesses": []
}

def score(d):
    return 5000 * exp(-d/scores[REGION])

def play_game(n_games):
    if LOAD_GAME:
        a = BirdAPI(None, None, gameinfo=json.loads(LOAD_GAME))
    else:
        a = BirdAPI(regions[REGION], n_games)
    g = None
    s = []
    for i in range(n_games):
        print(a.get_checklist(), end="")
        lon, lat, name = a.get_location()

        if g is None:
            g = GMap(views[REGION])

        guess = g.wait_click_pin()
        g.show_true(guess, (lon, lat))
        print(name)
        dist = g.distance(guess, (lon, lat))

        gameinfo["Guesses"].append(guess)

        s.append(score(dist))
        print(f"{s[-1]:0.0f} points. Your guess was off by distance {g.distance(guess, (lon, lat)):.2f} km")
        if i+1 == n_games or input(f"Continue game? You just finished round {i+1} out of {n_games} (Y/n): ") == "n":
            break
        g.reset()
    
    gameinfo["Checklists"].extend(a.checklist_codes)
    input(f"Your total score was {sum(s):0.0f}/{5000 * (i+1)}. Press enter to exit the game.")
    g.close()

play_game(N_GAMES)
print("Share the game:", gameinfo)
