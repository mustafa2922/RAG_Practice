import requests
import unicodedata
from bs4 import BeautifulSoup
import re

url =   "https://www.fatwaqa.com/ur/fatawa/hajj-aur-umrah/bete-ke-paison-se-hajj"

tasmiya_pattern = r'بسم\s*الل[هہھ]\s*الرحم[ٰ]?[نں]\s*الرح[یيى]م'

start_pattern =  r'الجواب\s*بعون\s*الملک\s*الوھاب'
end_pattern = r'و\s*اللہ\s*اعلم\s*عز\s*و\s*جل\s*و\s*رسولہ\s*اعلم'
question_title = r'سوال'
answer_title = 'جواب'

ANSWER_START = 'بِسْمِ اللہِ الرَّحْمٰنِ الرَّحِیْمِ اَلْجَوَابُ بِعَوْنِ الْمَلِکِ الْوَھَّابِ'
ANSWER_END = 'وَاللہُ اَعْلَمُ عَزَّوَجَلَّ وَرَسُوْلُہ اَعْلَم صَلَّی اللہُ تَعَالٰی عَلَیْہِ وَاٰلِہٖ وَسَلَّم'

# ===================================== utility functions ======================================

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

def extract_fatwa_data(html_content):
   
   soup = BeautifulSoup(html_content , 'html.parser')

   text = soup.get_text()
   # Replace non-breaking spaces and weird unicode spaces
   text = text.replace('\xa0', ' ').replace('\u200c', '').replace('\u200f', '')
   # Replace multiple newlines and tabs with a single space
   text = re.sub(r'[\r\n\t]+', ' ', text)
   # Replace multiple spaces with one
   text = re.sub(r'\s+', ' ', text)
   
   text = unicodedata.normalize("NFD", text)
   # Remove all combining marks (Arabic harakat)
   text = re.sub(r'[\u064B-\u0652]', '', text, flags=re.UNICODE)
   
   return unicodedata.normalize("NFC", text)

# ================================= single unit run ======================================

html = extract_fatwa_HTML(url)

text = extract_fatwa_data(html)

first_split = re.split(question_title,text)

second_split = re.split(start_pattern,first_split[1])

question = second_split[0]
question = question.replace(answer_title,'')
question = re.sub(tasmiya_pattern,'',question)

print(question)
print()

third_split = re.split(end_pattern,second_split[1])

answer = third_split[0]
answer = ANSWER_START + answer + ANSWER_END

print(answer)

# ===================================================================

Ten_URLS = [ "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/fajr-ki-sunnat-reh-jana",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/quran-pak-par-airab",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/quran-pak-tarjuma-record-karwana",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/meher-kam-se-kam-miqdar-hadees",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/quran-mushriqain-maghribain-matlab",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/jora-sadaqah-karna-hadees",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/chalte-phirte-tilawat",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/quran-ko-makhlooq-kehna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/musalman-ko-gali-dena-hadees-sharah",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/imam-ka-gardanen-phalangna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/fajir-ke-peeche-namaz",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/toba-karne-wale",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/quran-se-unchi-jaga-bethna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/panch-waqt-ki-namaz-quran-mein-zikr",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/quran-pak-parhna-afzal-hai-ya-sunna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/nasab-badalne-wale-par-jannat-haram-hone-ka-matlab",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/yusha-kon-hain",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/ek-qurani-ayat-ki-tafseer",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/surah-mulk-maghrib-se-pehle-parhna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/allah-ki-bande-se-mohabbat",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/bewazu-page-par-ayat-e-qurani-likhna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/baal-rangne-mein-yahood-nasara-ki-mukhalfat",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/tilawat-mein-naam-e-muhammad-aane-par-anguthe-chumna",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/dua-hizbul-bahr-parhna-kaisa",
  "https://www.fatwaqa.com/ur/fatawa/quran-aur-hadees/kya-rozana-kangi-karna-mana-hai",]
 
# for url in Ten_URLS:
#     html = extract_fatwa_HTML(url)

#     text = extract_fatwa_data(html)

#     first_split = re.split(question_title,text)

#     question = re.split(start_pattern,first_split[1])[0]
#     question = question.replace(answer_title,'')
#     question = re.sub(tasmiya_pattern,'',question)

#     print(question)
#     print()