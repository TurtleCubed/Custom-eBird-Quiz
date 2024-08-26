import sounddevice as sd
from librosa import load
import os
import numpy as np

codes = {
    "amre": "American Redstart",
    "baww": "Black-and-white Warbler",
    "bbwa": "Bay-breasted Warbler",
    "blbw": "Blackburnian Warbler",
    "blpw": "Blackpoll Warbler",
    "btb": "Black-throated Blue Warbler",
    "btg": "Black-throated Green Warbler",
    "bwwa": "Blue-winged Warbler",
    "cawa": "Canada Warbler",
    "cewa": "Cerulean Warbler",
    "chsp": "Chipping Sparrow",
    "cmwa": "Cape May Warbler",
    "coye": "Common Yellowthroat",
    "cswa": "Chestnut-sided Warbler",
    "deju": "Dark-eyed Junco",
    "howa": "Hooded Warbler",
    "inbu": "Indigo Bunting",
    "lowa": "Louisiana Waterthrush",
    "mawa": "Magnolia Warbler",
    "mowa": "Mourning Warbler",
    "nawa": "Nashville Warbler",
    "nowa": "Northern Waterthrush",
    "nopa": "Northern Parula",
    "ocwa": "Orange-crowned Warbler",
    "oven": "Ovenbird",
    "pawa": "Palm Warbler",
    "prow": "Prothonotary Warbler",
    "prwa": "Prairie Warbler",
    "tewa": "Tennessee Warbler",
    "wiwa": "Wilson's Warbler",
    "yewa": "Yellow Warbler",
    "yrwa": "Yellow-rumped Warbler",
    "ytwa": "Yellow-throated Warbler",
    "wewa": "Worm-eating Warbler",
}


if __name__=="__main__":
    files = set(os.listdir("songs"))
    birds = list(codes.keys())
    while True:
        bird = np.random.choice(birds, size=1)[0]
        i = -1
        fname = f'{bird}_{i}.mp3'
        while fname not in files:
            i = np.random.randint(0, 7)
            fname = f'{bird}_{i}.mp3'

        audio, sr = load(os.path.join('songs', fname))
        audio = np.pad(audio, (sr * 3, 0), "constant", constant_values=0)
        audio = np.tile(audio, 3)
        user_input = ""
        while user_input != "a":
            sd.play(audio, sr)
            user_input = input("Input a for the answer, anything else to replay: ")
        print(codes[fname.split("_")[0]], i)
