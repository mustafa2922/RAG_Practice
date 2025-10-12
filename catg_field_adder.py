# I forgot to include category initially, thats why used this script lmfao

import json
CATEGORY_INDEX = 5

def extract_category(url):

    category = url.split('/')[CATEGORY_INDEX]
    return category

with open('./fatwa_data/raw_fatwas.json','r',encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    item['category'] = extract_category(item['url'])

with open('./fatwa_data/raw_fatwas.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)