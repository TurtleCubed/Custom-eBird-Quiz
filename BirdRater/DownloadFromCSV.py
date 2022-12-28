import requests
import os
from PIL import Image, UnidentifiedImageError
import csv
from tqdm import tqdm

def read_csv(name):
    ml_nums = []
    ratings = []
    with open(name, mode ='r', encoding="utf-8") as file:
        csvFile = csv.reader(file)

        # skip header line
        x = next(csvFile)
        # print(list(enumerate(x)))
        for lines in csvFile:
            ml_nums.append(lines[0])
            ratings.append(lines[40])
            if int(ml_nums[-1]) == 724555:
                break
    return ml_nums, ratings

def save_img(ml_num, rating, qual=75, redown=False):
    if not redown and os.path.isfile(f'PhotoLibrary/{ml_num}_{rating}.jpg'):
        return
    request = requests.get(f"https://cdn.download.ams.birds.cornell.edu/api/v1/asset/{ml_num}/2400", stream=True)
    try:
        img = Image.open(request.raw) # np.array(Image.open(request.raw))
        img.convert("RGB").save(f'./BirdRater/PhotoLibrary/{ml_num}_{float(rating):.2f}.jpg', format='JPEG', quality=qual)
    except UnidentifiedImageError as e:
        print(ml_num)

if __name__=="__main__":
    from multiprocessing import Pool, freeze_support
    nums, ratings = read_csv('./BirdRater/Tristan_test_set.csv')
    freeze_support()
    with Pool(8) as pool:
        pool.starmap(save_img, tqdm(zip(nums, ratings), total=len(nums)))
    # for i in range(len(nums)):
    #     save_img(nums[i], ratings[i])
