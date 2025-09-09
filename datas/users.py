import json


with open("users.json", "r", encoding="utf-8") as f:
    data = json.load(f)

with open("hududlar.json", "r", encoding="utf-8") as f:
    hududlar = json.load(f)




t = 0
m = 0
for user in data:
    if len(user['hududkod']) == 7:
        t += 1
        for hudud in hududlar:
            has = False
            for tuman in hudud['childs']:
                if tuman['tumankod'] == user['hududkod'][4:]:
                   has = True
                   break
            if has:
                m += 1
                break


print(f"Total users with 7 digit hududkod: {t}, {m}")