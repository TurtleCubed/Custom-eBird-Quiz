import numpy as np
import os
from skimage.io import imread
import torch
from torch.utils.data import Dataset, random_split

class RatedData(Dataset):
    train, val, test = None, None, None

    def __init__(self, root, train=True, val=False, transform=None, train_split=0.7, val_split=0.2, test_split=0.1):

        self._root = root
        self._transform = transform
        self._train = train

        if RatedData.train is None:

            self._data = []
            for filename in os.listdir(self._root):
                f = os.path.join(self._root, filename)
                if os.path.isfile(f):
                    rating = round(float(filename[filename.index('_') + 1:filename.index('_') + 5]))
                    self._data.append((imread(f), rating))

            SEED = 0
            RatedData.train, RatedData.val, RatedData.test = random_split(self._data, [train_split, val_split, test_split], generator=torch.Generator().manual_seed(SEED))

        if self._train:
            self._data = RatedData.train
        elif val:
            self._data = RatedData.val
        else:
            self._data = RatedData.test
        # print([x[1] for x in list(self._data)])

    def __len__(self):
        return len(self._data)

    def __getitem__(self, idx):
        img, rating = self._data[idx]
        rating -= 1
        if self._transform is not None:
            return self._transform(img), rating
        return img, rating

# x = RatedData("./BirdRater/tmp", train=True)
# y = RatedData("./BirdRater/tmp", train=False, val=True)
# z = RatedData("./BirdRater/tmp", train=False, val=False)
# print(len(x))
# print(len(y))
# print(len(z))
