import requests
import unicodedata
from bs4 import BeautifulSoup
import re

# ====================== constants ============================================================

tasmiya_pattern = r'بسم\s*الل[هہھ]\s*الرحم[ٰ]?[نں]\s*الرح[یيى]م'

start_pattern =  r'الجواب\s*بعون\s*الملک\s*الوھاب'
end_pattern = r'و\s*اللہ\s*اعلم\s*عز\s*و\s*جل\s*و\s*رسولہ\s*اعلم'

question_title = r'د[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ر[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ل[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ف[\u064B-\u0652\u0670]*\s*ت[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*ء[\u064B-\u0652\u0670]*\s*ا[\u064B-\u0652\u0670]*\s*[هہھۃ][\u064B-\u0652\u0670]*\s*ل[\u064B-\u0652\u0670]*\s*س[\u064B-\u0652\u0670]*\s*[نں][\u064B-\u0652\u0670]*\s*ت[\u064B-\u0652\u0670]*'
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

def extract_ques_ans(text):

    first_split = re.split(question_title,text)
    second_split = re.split(start_pattern,first_split[1])

    question = second_split[0]
    question = question.replace(answer_title,'')
    question = re.sub(tasmiya_pattern,'',question)
    question = question[question.find('سوال')+len('سوال'):]

    third_split = re.split(end_pattern,second_split[1])

    answer = third_split[0]
    answer = ANSWER_START + answer + ANSWER_END

    return {'question':question,'answer':answer}


# ===================================================================

Ten_URLS = ["https://www.fatwaqa.com/ur/fatawa/aqaid/musalman-ko-kafir-kehna-kaisa-kya-kehne-wala-kafir-hoga",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/hazrat-adam-ki-aulaad-hone-ki-bina-par-hindu-muslim-bhai-bhai-kehna",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/is-niyat-se-kalima-parhna-ke-kufriya-jumla-na-nikla-ho",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/ek-mashhoor-sher-ka-shari-hukum",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/kya-islam-mein-churail-ki-haqiqat-hai",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/pehle-ke-ulama-scientist-the-aaj-ke-kyun-nahi",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/ghair-e-nabi-ko-nabi-se-afzal-kehna-kaisa",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/hazrat-aisha-siddiqah-ki-pakdamni-ka-inkar-karne-wale-ka-hukum",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/big-bang-theory-kya-hai-iski-shari-hesiyat",
  "https://www.fatwaqa.com/ur/fatawa/aqaid/mein-kafir-ho-jaunga-kehne-ka-hukum"]
 
for url in Ten_URLS:
    html = extract_fatwa_HTML(url)

    text = extract_fatwa_data(html)

    print(extract_ques_ans(text))