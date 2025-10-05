import requests
import json
from bs4 import BeautifulSoup
import re
url = "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/fajr-ki-sunnat-reh-jana"

def extract_fatwa_HTML(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept-Language": "ur,en;q=0.9"
    }

    res = requests.get(url, headers=headers)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")

    capture_div = soup.find("div", id="captureDiv")

    if not capture_div:
        print("❌ No div with id='captureDiv' found.")
        return None

    return capture_div.prettify()

def extract_fatwa_data(html_content, url):
   
   soup = BeautifulSoup(html_content , 'html.parser')

   text = soup.get_text()
   # Replace non-breaking spaces and weird unicode spaces
   text = text.replace('\xa0', ' ').replace('\u200c', '').replace('\u200f', '')
   # Replace multiple newlines and tabs with a single space
   text = re.sub(r'[\r\n\t]+', ' ', text)
   # Replace multiple spaces with one
   text = re.sub(r'\s+', ' ', text)

   return(text)

def parse_fatwa(text: str) -> dict:
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Extract fields based on exact Urdu anchors
    title_match = re.search(r'^(.*?)دار ?الافتاء ?اھلسنت', text)
    question_match = re.search(r'سوال(.*?)جواب', text)
    answer_match = re.search(
        r'(بِسْمِ ?اللہِ ?الرَّحْمٰنِ ?الرَّحِيْمِ.*?و ?اللہُ ?اَعْلَمُ ?عَزَّ ?و ?جَلَّ ?و ?رَسُوْلُہ ?اَعْلَم ?صَلَّی ?اللہُ ?تَعَالٰی ?عَلَیْہِ ?و ?اٰلِہٖ ?و ?سَلَّم)',
        text
    )

    # Handle mufti + optional musaddiq
    mufti_block_match = re.search(r'مجيب[:：]?\s*(.*?)فتوی نمبر', text)
    mufti_name, musaddiq_name = None, None
    if mufti_block_match:
        block = mufti_block_match.group(1)
        mufti_split = re.split(r'مصدق[:：]?', block)
        mufti_name = mufti_split[0].strip() if mufti_split else None
        if len(mufti_split) > 1:
            musaddiq_name = mufti_split[1].strip()

    fatwa_no_match = re.search(r'فتوی نمبر[:：]?\s*(.*?)تاریخ ?اجراء', text)
    date_match = re.search(r'تاریخ ?اجراء[:：]?\s*(.*)$', text)

    # Build structured dictionary
    return {
        "title": title_match.group(1).strip() if title_match else None,
        "question": question_match.group(1).strip() if question_match else None,
        "answer": answer_match.group(1).strip() if answer_match else None,
        "mufti": mufti_name,
        "musaddiq": musaddiq_name,
        "fatwa_no": fatwa_no_match.group(1).strip() if fatwa_no_match else None,
        "date": date_match.group(1).strip() if date_match else None,
        "source": "دار الافتاء اھلسنت (دعوت اسلامی)"
    }
 
html = extract_fatwa_HTML(url)

text = extract_fatwa_data(html, url)

fatwa_obj = parse_fatwa(text)

print(fatwa_obj)

# print(json.dumps(result, ensure_ascii=False, indent=2))