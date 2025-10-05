import requests, html, json
from bs4 import BeautifulSoup

base_url = f"https://www.fatwaqa.com/ur/fatawa"

headers = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
}

categories = ['quran-aur-hadees', 'aqaid', 'mamoolat-e-ahlesunnat', 'taharat-ke-masail', 'namaz', 'mayyat', 'roza', 'zakat-aur-ushr', 'hajj-aur-umrah', 'qurbani-aur-aqeeqah', 'mukhtasar-jawabat', 'bachon-ke-naam', 'mahnama-ahkam-e-tijarat', 'masnoon-duayein', 'zibah-aur-shikar', 'qasam-aur-mannat', 'nikah', 'talaq', 'razaat', 'iddat', 'khareed-o-farokht', 'shirkat', 'muzaribat', 'ijarah', 'qarz-hiba-rahan', 'waqf', 'wirasat-aur-tarka', 'luqatah', 'saza-o-qaza', 'halal-haram', 'sunnatain-aur-adab', 'gunah', 'huqooq-ul-ibad', 'fazail-o-seerat', 'auraton-ke-masail', 'kafir-aur-murtad', 'majlis-e-tehqiqat-e-shariah', 'iqtisad', 'sadqa', 'mutafariqat']

all_urls = []

for category in categories:
    page = 1
    while True:
        url = f"{base_url}/{category}?page={page}"
        print(f"Scraping {url}")

        res = requests.get(url, headers=headers)
        res.encoding = 'utf-8'

        if res.status_code != 200:
            print("Failed:", res.status_code)
            break

        cleaned_html = html.unescape(res.text)
        cleaned_html = cleaned_html.replace('\\"', '"').replace("\\/", "/")

        soup = BeautifulSoup(cleaned_html, "html.parser")

        links = [
            a["href"]
            for a in soup.select(f"a[href*='/ur/fatawa/{category}/']")
        ]

        if not links:
            print("Done with category", category)
            break

        all_urls.extend(links)

        print("Found:", len(links))
        page += 1


output_path = "fatwa_urls.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(all_urls, f, ensure_ascii=False, indent=2)