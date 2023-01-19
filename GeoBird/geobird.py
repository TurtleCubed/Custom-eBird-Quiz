from checklist import BirdAPI
from map import GMap

region = "California"

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

def play_game():
    a = BirdAPI(regions[region])
    g = None
    while True:
        a.new_checklist()
        print(a.get_checklist(), end="")
        lon, lat, name = a.get_location()

        if g is None:
            g = GMap(views[region])

        guess = g.wait_click_pin()
        g.show_true(guess, (lon, lat))
        print(name)
        print(f"Your guess was off by distance {g.distance(guess, (lon, lat))} km")
        if input("new game (Y/n): ") == "n":
            g.close()
            break
        g.reset()

play_game()