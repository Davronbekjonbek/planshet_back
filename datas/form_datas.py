import requests
import json

headers = {
    "Authorization": "Token 28f417fc72d201c2cdfb3b6d65c4830c176e3675"
}

url = "https://kf.kobotoolbox.org/api/v2/assets/abuTTZJpsJ9ED9FW45ccy3/data.json"
res = requests.get(url, headers=headers)
data = res.json()


with open("form_datas.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

