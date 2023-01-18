import http.client
import json
from random import randint

conn = http.client.HTTPSConnection("api.ebird.org")
payload = ''
headers = {
  'X-eBirdApiToken': '6c8plv8d6h6b'
}

def lookup(url):
	conn.request("GET", url, payload, headers)
	res = conn.getresponse()
	data = res.read()
	return data.decode('utf-8')

def taxonomy(spcode):
    return lookup(f"/v2/ref/taxonomy/ebird?species={spcode}").split(",")[15]
y = 2022
m = randint(1, 12)
d = randint(1, 28)
CA = f"/v2/product/lists/US-CA/2022/{m}/{d}?maxResults=200"#f"/v2/product/lists/US/2022/{m}/{d}?maxResults=200"
a = json.loads(lookup(CA))
# print(a)

for i in range(len(a)):
	conn.request("GET", f"/v2/product/checklist/view/{a[i]['subID']}", payload, headers)
	res = conn.getresponse()
	data = res.read()
	b = json.loads(data.decode("utf-8"))
	if len(b["obs"]) >= 30 and lookup(f"/v2/ref/hotspot/info/{b['locId']}"):
		for sp in b["obs"]:
			# print(sp)
			print(sp["howManyAtleast"], taxonomy(sp["speciesCode"]))
		break
# print(b)
# print("mission failed")
input("Press enter for date")
print(f"{y}/{m}/{d}")
input("Press enter for location")
hotspot = lookup(f"/v2/ref/hotspot/info/{b['locId']}")
print(hotspot)

# print(lookup("/v2/ref/region/list/subnational2/US-CA"))
