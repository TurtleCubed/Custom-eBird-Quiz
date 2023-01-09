import os
import time
from shutil import copy2
from tqdm import tqdm
import filecmp

# Set to True for an extra folder to put RAW photos
SPECIAL_RAW = True
# Set to True to prompt for location to append to folder name
LOCATION = False
# Set ERASE to True to erase files when finished importing. SAFE double checks the file was copied properly but is slower.
ERASE = True
SAFE = True
# SD Card location 
SD_CARD = "E:\\DCIM\\100CANON\\"
# Location to import photos to
IMPORT_TO = os.getcwd()

def time_to_date(t):
    return time.strftime("%Y-%m-%d", time.strptime(time.ctime(t)))

if __name__=='__main__':
    date_to_loc = {}
    list_dir = list(os.listdir(SD_CARD))

    if LOCATION:
        for filename in os.listdir(SD_CARD):
            filepath = os.path.join(SD_CARD, filename)
            format_date = time_to_date(os.path.getmtime(filepath))
            if format_date not in date_to_loc:
                date_to_loc[format_date] = input(f"Please enter the location for {format_date}: ")

    for filename in tqdm(os.listdir(SD_CARD)):
        filepath = os.path.join(SD_CARD, filename)
        format_date = time_to_date(os.path.getmtime(filepath))
        folder = os.path.join(IMPORT_TO, format_date)

        if LOCATION:
            folder = os.path.join(IMPORT_TO, format_date + " " + date_to_loc[format_date])

        if not os.path.isdir(folder):
            os.mkdir(folder)

        if SPECIAL_RAW and filename.endswith(".CR3"):
            folder = os.path.join(folder, "raw " + format_date)
            if not os.path.isdir(folder):
                os.mkdir(folder)

        out_path = os.path.join(folder, filename)

        copy2(filepath, out_path)

        if ERASE:
            if SAFE: # Hardcore 
                assert filecmp.cmp(filepath, out_path)
            os.remove(filepath)
