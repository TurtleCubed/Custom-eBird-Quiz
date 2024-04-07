import csv

def life_list(csv_filename):
    life = set()
    with open(csv_filename, encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        next(reader, None) # skip heading
        for row in reader:
            life.add(row[1].strip())
    return life

def aba_codes(aba_filename):
    # Get csv from https://www.aba.org/aba-checklist/
    aba = {}
    with open(aba_filename, encoding='utf-8') as csv_file:
        reader = csv.reader(csv_file)
        for i in range(4): next(reader) # skip heading
        for row in reader:
            if row[5]:
                aba[row[1]] = int(row[5])
    return aba

both_lists = life_list("./Scripts/Aaron.csv").intersection(life_list("./Scripts/Tristan.csv"))
aba = aba_codes("./Scripts/ABA_Checklist-8.12.csv")


by_code = [set() for _ in range(6)]
for k, v in aba.items():
    by_code[v - 1].add(k)

missing = [set() for _ in range(2)]
for rarity_code in range(2):
    for sp in by_code[rarity_code]:
        if sp not in both_lists:
            missing[rarity_code].add(sp)

print(missing)
print(len(missing[0]), len(missing[1]))